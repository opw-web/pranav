"""Ties the deterministic parser + categorizer + account/category token resolution
together into one resolved preview, used by both the live-preview and commit routes
so they can never disagree with each other."""

from rapidfuzz import fuzz, process
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.balances import get_account_balances
from app.services.categories import get_grouped_tree
from app.services.categorizer import categorize
from app.services.quickadd_parser import ParsedQuickAdd, parse_quickadd


def _flatten_tree(tree):
    flat = []
    for g in tree:
        flat.append({"id": str(g["id"]), "name": g["name"], "label": g["name"]})
        for c in g["children"]:
            flat.append({"id": str(c["id"]), "name": c["name"], "label": f"{g['name']} › {c['name']}"})
    return flat


async def _resolve_account(session: AsyncSession, user_id: str, token: str | None):
    accounts = await get_account_balances(session, user_id)
    if not accounts:
        return None
    if not token:
        last_id = (
            await session.execute(
                text(
                    "SELECT account_id FROM transactions WHERE user_id = :uid AND is_deleted = FALSE "
                    "ORDER BY created_at DESC LIMIT 1"
                ),
                {"uid": user_id},
            )
        ).scalar()
        if last_id:
            match = next((a for a in accounts if str(a["id"]) == str(last_id)), None)
            if match:
                return match
        return accounts[0]

    best = process.extractOne(token, [a["name"] for a in accounts], scorer=fuzz.WRatio)
    if best and best[1] >= 60:
        return next(a for a in accounts if a["name"] == best[0])
    return accounts[0]


def _resolve_forced_category(flat_categories: list[dict], token: str | None):
    if not token or not flat_categories:
        return None
    best = process.extractOne(token, [c["name"] for c in flat_categories], scorer=fuzz.WRatio)
    if best and best[1] >= 60:
        return next(c for c in flat_categories if c["name"] == best[0])
    return None


def _label_for(flat_categories: list[dict], category_id: str | None) -> str | None:
    if not category_id:
        return None
    match = next((c for c in flat_categories if c["id"] == category_id), None)
    return match["label"] if match else None


async def build_quickadd_preview(session: AsyncSession, user_id: str, raw: str) -> dict:
    parsed: ParsedQuickAdd = parse_quickadd(raw)
    tree = await get_grouped_tree(session, user_id)
    flat_categories = _flatten_tree(tree)

    account = await _resolve_account(session, user_id, parsed.account_token)
    forced = _resolve_forced_category(flat_categories, parsed.category_token)

    category_id = None
    category_label = "Uncategorized"
    merchant_clean = parsed.merchant_token
    confidence = "none"

    if forced:
        category_id = forced["id"]
        category_label = forced["label"]
    elif parsed.merchant_token:
        result = await categorize(session, user_id, parsed.merchant_token)
        merchant_clean = result["merchant_clean"] or parsed.merchant_token
        category_id = result["category_id"]
        confidence = result["confidence"]
        label = _label_for(flat_categories, category_id)
        if label:
            category_label = label

    return {
        "parsed": parsed,
        "account": account,
        "category_id": category_id,
        "category_label": category_label,
        "merchant_clean": merchant_clean,
        "confidence": confidence,
    }
