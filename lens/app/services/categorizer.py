"""Deterministic categorizer (§4.1) — the shipped "AI" that is actually just rules + fuzzy match.

categorize(merchant_raw, user_id) -> {merchant_clean, category_id, confidence}
    1. User rules first (categorization_rules), by priority. First hit wins.
    2. Shipped merchant dictionary (merchant_seed), fuzzy-matched with RapidFuzz.
    3. Miss -> Uncategorized. Never guess wildly.

Learning (the "always categorize X as Y" flow that writes a categorization_rules row
on correction) lives in routers/rules.py — this module only reads rules, it doesn't write them.
"""

import re
import uuid

from rapidfuzz import fuzz, process
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.categories import get_grouped_tree

FUZZY_THRESHOLD = 88
# User-taught rules must beat the shipped seed. Seed matches are applied at runtime
# (not stored as rules), so any user rule with priority < 100 wins by construction;
# we default learned rules to 50 to leave headroom above and below for manual tuning.
LEARNED_RULE_PRIORITY = 50


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


async def resolve_category_key(session: AsyncSession, user_id: str, category_key: str) -> str | None:
    """Maps a shipped seed's 'food.restaurants' key to this user's actual category id,
    by slugifying their (editable) category names. Falls back gracefully if the user
    has renamed/deleted the category — never raises, just returns None (Uncategorized)."""
    parts = category_key.split(".")
    tree = await get_grouped_tree(session, user_id)
    parent = next((g for g in tree if slugify(g["name"]) == parts[0]), None)
    if parent is None:
        return None
    if len(parts) == 1:
        return str(parent["id"])
    child = next((c for c in parent["children"] if slugify(c["name"]) == parts[1]), None)
    return str(child["id"]) if child else str(parent["id"])


async def categorize(session: AsyncSession, user_id: str, merchant_raw: str | None) -> dict:
    if not merchant_raw or not merchant_raw.strip():
        return {"merchant_clean": None, "category_id": None, "confidence": "none"}

    merchant_raw = merchant_raw.strip()

    rules = (
        await session.execute(
            text(
                "SELECT id, match_type, pattern, set_merchant, set_category_id FROM categorization_rules "
                "WHERE user_id = :uid ORDER BY priority ASC"
            ),
            {"uid": user_id},
        )
    ).mappings().all()

    for rule in rules:
        pattern = rule["pattern"]
        if rule["match_type"] == "exact":
            matched = merchant_raw.lower() == pattern.lower()
        elif rule["match_type"] == "contains":
            matched = pattern.lower() in merchant_raw.lower()
        elif rule["match_type"] == "regex":
            try:
                matched = re.search(pattern, merchant_raw, re.IGNORECASE) is not None
            except re.error:
                matched = False
        else:
            matched = False

        if matched:
            await session.execute(
                text("UPDATE categorization_rules SET times_applied = times_applied + 1 WHERE id = :id"),
                {"id": rule["id"]},
            )
            return {
                "merchant_clean": rule["set_merchant"] or merchant_raw,
                "category_id": str(rule["set_category_id"]) if rule["set_category_id"] else None,
                "confidence": "high",
            }

    seed_rows = (
        await session.execute(text("SELECT pattern, merchant_clean, category_key FROM merchant_seed"))
    ).mappings().all()

    if seed_rows:
        choices = {row["pattern"]: row for row in seed_rows}
        best = process.extractOne(merchant_raw.lower(), list(choices.keys()), scorer=fuzz.token_set_ratio)
        if best and best[1] >= FUZZY_THRESHOLD:
            matched_row = choices[best[0]]
            category_id = await resolve_category_key(session, user_id, matched_row["category_key"])
            return {"merchant_clean": matched_row["merchant_clean"], "category_id": category_id, "confidence": "medium"}

    return {"merchant_clean": merchant_raw, "category_id": None, "confidence": "none"}


def _learn_pattern(merchant_raw: str) -> str:
    """Derive a stable 'contains' pattern from a raw merchant string, e.g.
    'AMZN MKTP IN*1A2B3 MUMBAI' -> 'amzn mktp in'. We keep the leading alphabetic
    tokens (the brand) and drop trailing transaction ids/city noise so the rule
    generalises to the next statement line from the same merchant."""
    tokens = re.findall(r"[A-Za-z]+", merchant_raw)
    kept = []
    for tok in tokens:
        kept.append(tok.lower())
        if len(kept) >= 3:
            break
    return " ".join(kept) if kept else merchant_raw.strip().lower()


async def learn_rule(
    session: AsyncSession,
    user_id: str,
    merchant_raw: str,
    category_id: str | None,
    set_merchant: str | None = None,
) -> dict:
    """Create (or update) a user categorization rule from a correction (§4.1 step 4).
    Idempotent per (user, pattern): re-teaching the same merchant updates the target
    rather than piling up duplicate rules."""
    pattern = _learn_pattern(merchant_raw)
    existing = (
        await session.execute(
            text(
                "SELECT id FROM categorization_rules "
                "WHERE user_id = :uid AND match_type = 'contains' AND lower(pattern) = :pat"
            ),
            {"uid": user_id, "pat": pattern},
        )
    ).scalar()

    if existing:
        await session.execute(
            text(
                "UPDATE categorization_rules SET set_category_id = :cid, set_merchant = :m WHERE id = :id"
            ),
            {"cid": category_id, "m": set_merchant, "id": existing},
        )
        rule_id = str(existing)
    else:
        rule_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO categorization_rules "
                "(id, user_id, match_type, pattern, set_merchant, set_category_id, priority) "
                "VALUES (:id, :uid, 'contains', :pat, :m, :cid, :prio)"
            ),
            {
                "id": rule_id,
                "uid": user_id,
                "pat": pattern,
                "m": set_merchant,
                "cid": category_id,
                "prio": LEARNED_RULE_PRIORITY,
            },
        )
    return {"rule_id": rule_id, "pattern": pattern}


async def back_apply_rule(
    session: AsyncSession, user_id: str, pattern: str, category_id: str | None
) -> int:
    """Apply a freshly-learned rule to existing *uncategorized* transactions whose
    merchant_raw contains the pattern (§4.1 step 4, 'ask first' — the caller gates this).
    Only touches uncategorized rows so we never silently overwrite the user's own choices."""
    result = await session.execute(
        text(
            "UPDATE transactions SET category_id = :cid, updated_at = now() "
            "WHERE user_id = :uid AND is_deleted = FALSE AND category_id IS NULL "
            "AND position(:pat in lower(merchant_raw)) > 0"
        ),
        {"cid": category_id, "uid": user_id, "pat": pattern},
    )
    return result.rowcount or 0
