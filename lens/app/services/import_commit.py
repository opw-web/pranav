"""DB-touching import steps: dedupe lookup, per-row categorize, transfer-link, chunked insert.
Kept separate from importer.py (pure detection/parsing) so the parsing stays DB-free/testable.
"""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import importer
from app.services.categorizer import categorize


async def existing_dedupe_hashes(session: AsyncSession, user_id: str, account_id: str) -> set[str]:
    rows = await session.execute(
        text(
            "SELECT dedupe_hash FROM transactions "
            "WHERE user_id = :uid AND account_id = :aid AND dedupe_hash IS NOT NULL"
        ),
        {"uid": user_id, "aid": account_id},
    )
    return {r[0] for r in rows}


async def build_preview(session: AsyncSession, user_id: str, account_id: str, txns: list[dict]) -> dict:
    """Annotate parsed rows with dedupe + transfer flags for the preview table (§5.3 step 4)."""
    seen_db = await existing_dedupe_hashes(session, user_id, account_id)
    seen_batch: set[str] = set()
    transfer_pairs = dict(importer.find_transfer_pairs(txns))
    transfer_idxs = set(transfer_pairs.keys()) | set(transfer_pairs.values())

    annotated = []
    dupes = 0
    for i, t in enumerate(txns):
        h = importer.dedupe_hash(account_id, t["txn_date"], t["amount"], t["merchant_raw"] or "")
        is_dupe = h in seen_db or h in seen_batch
        seen_batch.add(h)
        if is_dupe:
            dupes += 1
        annotated.append({**t, "dedupe_hash": h, "is_duplicate": is_dupe, "is_transfer": i in transfer_idxs})

    return {
        "rows": annotated,
        "total": len(txns),
        "duplicates": dupes,
        "transfers": len(transfer_pairs),
        "to_import": len(txns) - dupes,
    }


async def commit_chunk(
    session: AsyncSession,
    user_id: str,
    account_id: str,
    batch_id: str,
    txns: list[dict],
    start: int,
    end: int,
) -> dict:
    """Insert rows [start:end): skip duplicates, categorize each, link transfer legs.
    Returns per-chunk counts. Idempotent on re-run because dedupe_hash blocks repeats."""
    seen_db = await existing_dedupe_hashes(session, user_id, account_id)
    transfer_pairs = dict(importer.find_transfer_pairs(txns))
    # map each transfer index to its partner so we can tag the linkage
    partner = {}
    for a, b in transfer_pairs.items():
        partner[a] = b
        partner[b] = a

    imported = skipped = needs_review = 0
    for i in range(start, end):
        t = txns[i]
        h = importer.dedupe_hash(account_id, t["txn_date"], t["amount"], t["merchant_raw"] or "")
        if h in seen_db:
            skipped += 1
            continue
        seen_db.add(h)

        cat = await categorize(session, user_id, t["merchant_raw"])
        if cat["category_id"] is None:
            needs_review += 1

        is_transfer = i in partner
        txn_type = "transfer" if is_transfer else t["type"]
        transfer_group = None
        if is_transfer:
            # stable group id per unordered pair, so both legs share it across chunks
            lo, hi = sorted((i, partner[i]))
            transfer_group = str(uuid.uuid5(uuid.UUID(batch_id), f"{lo}-{hi}"))

        await session.execute(
            text(
                "INSERT INTO transactions "
                "(id, user_id, account_id, type, amount, currency, txn_date, merchant_raw, merchant_clean, "
                " category_id, source, import_batch_id, dedupe_hash, transfer_group_id) "
                "VALUES (:id,:uid,:aid,:type,:amount,'INR',:d,:mraw,:mclean,:cat,'import',:batch,:hash,:tgroup)"
            ),
            {
                "id": str(uuid.uuid4()),
                "uid": user_id,
                "aid": account_id,
                "type": txn_type,
                "amount": t["amount"],
                "d": t["txn_date"],
                "mraw": t["merchant_raw"],
                "mclean": cat["merchant_clean"],
                "cat": cat["category_id"] if not is_transfer else None,
                "batch": batch_id,
                "hash": h,
                "tgroup": transfer_group,
            },
        )
        imported += 1

    await session.execute(
        text(
            "UPDATE import_batches SET imported_count = imported_count + :imp, "
            "skipped_count = skipped_count + :skp WHERE id = :bid AND user_id = :uid"
        ),
        {"imp": imported, "skp": skipped, "bid": batch_id, "uid": user_id},
    )
    return {"imported": imported, "skipped": skipped, "needs_review": needs_review}


async def save_column_mapping(session, user_id, signature, mapping, date_format, amount_convention):
    """Remember this bank's format so the next import skips straight to preview (§5.3 step 3)."""
    import json

    await session.execute(
        text(
            "INSERT INTO column_mappings (id, user_id, bank_signature, mapping, date_format, amount_convention) "
            "VALUES (:id,:uid,:sig,CAST(:map AS JSONB),:df,:ac) "
            "ON CONFLICT (user_id, bank_signature) DO UPDATE SET "
            "mapping = EXCLUDED.mapping, date_format = EXCLUDED.date_format, "
            "amount_convention = EXCLUDED.amount_convention"
        ),
        {
            "id": str(uuid.uuid4()),
            "uid": user_id,
            "sig": signature,
            "map": json.dumps(mapping),
            "df": date_format,
            "ac": amount_convention,
        },
    )


async def recall_column_mapping(session, user_id, signature):
    row = (
        await session.execute(
            text(
                "SELECT mapping, date_format, amount_convention FROM column_mappings "
                "WHERE user_id = :uid AND bank_signature = :sig"
            ),
            {"uid": user_id, "sig": signature},
        )
    ).mappings().first()
    return dict(row) if row else None
