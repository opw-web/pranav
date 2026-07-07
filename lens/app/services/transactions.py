import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

LIST_SQL_BASE = """
SELECT t.id, t.account_id, a.name AS account_name, t.type, t.amount, t.currency,
       t.txn_date, t.merchant_raw, t.merchant_clean, t.category_id,
       c.name AS category_name, c.color AS category_color, c.icon AS category_icon,
       pc.name AS parent_category_name,
       t.notes, t.transfer_account_id, ta.name AS transfer_account_name,
       t.is_reimbursable, t.source, tags_agg.tags_csv
FROM transactions t
JOIN accounts a ON a.id = t.account_id
LEFT JOIN categories c ON c.id = t.category_id
LEFT JOIN categories pc ON pc.id = c.parent_id
LEFT JOIN accounts ta ON ta.id = t.transfer_account_id
LEFT JOIN LATERAL (
    SELECT string_agg(tg.name, ',' ORDER BY tg.name) AS tags_csv
    FROM transaction_tags tt JOIN tags tg ON tg.id = tt.tag_id
    WHERE tt.transaction_id = t.id
) tags_agg ON true
WHERE t.user_id = :uid AND t.is_deleted = FALSE
"""

UPDATABLE_FIELDS = {"txn_date", "merchant_clean", "amount", "notes", "category_id", "type"}


async def list_transactions(session: AsyncSession, user_id: str, filters: dict, limit: int = 200):
    sql = LIST_SQL_BASE
    params = {"uid": user_id}

    if filters.get("account_id"):
        sql += " AND t.account_id = :account_id"
        params["account_id"] = filters["account_id"]
    if filters.get("category_id"):
        sql += " AND t.category_id = :category_id"
        params["category_id"] = filters["category_id"]
    if filters.get("uncategorized"):
        sql += " AND t.category_id IS NULL"
    if filters.get("type"):
        sql += " AND t.type = :type"
        params["type"] = filters["type"]
    if filters.get("date_from"):
        sql += " AND t.txn_date >= :date_from"
        params["date_from"] = filters["date_from"]
    if filters.get("date_to"):
        sql += " AND t.txn_date <= :date_to"
        params["date_to"] = filters["date_to"]
    if filters.get("q"):
        sql += " AND (t.merchant_clean ILIKE :q OR t.merchant_raw ILIKE :q OR t.notes ILIKE :q)"
        params["q"] = f"%{filters['q']}%"

    sql += " ORDER BY t.txn_date DESC, t.created_at DESC LIMIT :limit"
    params["limit"] = limit

    result = await session.execute(text(sql), params)
    return result.mappings().all()


async def get_transaction(session: AsyncSession, user_id: str, txn_id: str):
    result = await session.execute(text(LIST_SQL_BASE + " AND t.id = :tid"), {"uid": user_id, "tid": txn_id})
    return result.mappings().first()


async def find_possible_duplicate(session, user_id, account_id, amount, merchant, txn_date, exclude_id=None) -> bool:
    """§5.1 duplicate guard: same amount + merchant + day on the same account. Never blocks — only warns."""
    sql = (
        "SELECT id FROM transactions WHERE user_id=:uid AND account_id=:aid AND amount=:amount "
        "AND txn_date=:txn_date AND is_deleted=FALSE AND COALESCE(merchant_raw,'')=:merchant"
    )
    params = {"uid": user_id, "aid": account_id, "amount": amount, "txn_date": txn_date, "merchant": merchant or ""}
    if exclude_id:
        sql += " AND id != :exclude_id"
        params["exclude_id"] = exclude_id
    result = await session.execute(text(sql), params)
    return result.first() is not None


async def create_transaction(
    session: AsyncSession,
    user_id: str,
    *,
    account_id: str,
    type: str,
    amount: float,
    txn_date,
    merchant_raw: str | None = None,
    merchant_clean: str | None = None,
    category_id: str | None = None,
    notes: str | None = None,
    transfer_account_id: str | None = None,
    currency: str = "INR",
    source: str = "manual",
) -> tuple[str, bool]:
    is_dup = await find_possible_duplicate(session, user_id, account_id, amount, merchant_raw, txn_date)
    txn_id = str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO transactions (id, user_id, account_id, type, amount, currency, txn_date, "
            "merchant_raw, merchant_clean, category_id, notes, transfer_account_id, source) "
            "VALUES (:id, :uid, :aid, :type, :amount, :currency, :txn_date, :mraw, :mclean, :cat, :notes, :tacc, :source)"
        ),
        {
            "id": txn_id, "uid": user_id, "aid": account_id, "type": type, "amount": amount,
            "currency": currency, "txn_date": txn_date, "mraw": merchant_raw, "mclean": merchant_clean,
            "cat": category_id, "notes": notes, "tacc": transfer_account_id, "source": source,
        },
    )
    return txn_id, is_dup


async def update_transaction(session: AsyncSession, user_id: str, txn_id: str, fields: dict):
    set_clauses = []
    params = {"uid": user_id, "tid": txn_id}
    for key, value in fields.items():
        if key not in UPDATABLE_FIELDS or value is None:
            continue
        set_clauses.append(f"{key} = :{key}")
        params[key] = value
    if not set_clauses:
        return
    set_clauses.append("updated_at = now()")
    sql = f"UPDATE transactions SET {', '.join(set_clauses)} WHERE id = :tid AND user_id = :uid"
    await session.execute(text(sql), params)


async def soft_delete_transaction(session: AsyncSession, user_id: str, txn_id: str):
    await session.execute(
        text("UPDATE transactions SET is_deleted = TRUE WHERE id = :tid AND user_id = :uid"),
        {"tid": txn_id, "uid": user_id},
    )


async def restore_transaction(session: AsyncSession, user_id: str, txn_id: str):
    await session.execute(
        text("UPDATE transactions SET is_deleted = FALSE WHERE id = :tid AND user_id = :uid"),
        {"tid": txn_id, "uid": user_id},
    )


async def bulk_delete(session: AsyncSession, user_id: str, txn_ids: list[str]):
    for txn_id in txn_ids:
        await soft_delete_transaction(session, user_id, txn_id)


async def bulk_set_category(session: AsyncSession, user_id: str, txn_ids: list[str], category_id: str | None):
    # Bypasses update_transaction's "None means not-provided" convention: here None is a
    # deliberate "set to Uncategorized", so it must be written explicitly.
    for txn_id in txn_ids:
        await session.execute(
            text("UPDATE transactions SET category_id = :cat, updated_at = now() WHERE id = :tid AND user_id = :uid"),
            {"cat": category_id, "tid": txn_id, "uid": user_id},
        )
