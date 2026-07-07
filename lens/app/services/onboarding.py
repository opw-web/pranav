import json
import os
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CATEGORIES_SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "seeds", "categories_default.json")


async def ensure_onboarded(session: AsyncSession, user_id: str):
    """First-login seed (§4.6): starter category tree + a default Cash account.
    Idempotent — no-ops if the user already has any accounts."""
    existing = await session.execute(text("SELECT 1 FROM accounts WHERE user_id = :uid LIMIT 1"), {"uid": user_id})
    if existing.first() is not None:
        return

    with open(CATEGORIES_SEED_PATH, encoding="utf-8") as f:
        tree = json.load(f)

    for parent in tree:
        parent_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO categories (id, user_id, name, parent_id, kind, color, icon, is_system) "
                "VALUES (:id, :uid, :name, NULL, :kind, :color, :icon, TRUE)"
            ),
            {
                "id": parent_id,
                "uid": user_id,
                "name": parent["name"],
                "kind": parent["kind"],
                "color": parent.get("color"),
                "icon": parent.get("icon"),
            },
        )
        for child in parent.get("children", []):
            await session.execute(
                text(
                    "INSERT INTO categories (id, user_id, name, parent_id, kind, color, icon, is_system) "
                    "VALUES (:id, :uid, :name, :parent_id, :kind, :color, :icon, TRUE)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "uid": user_id,
                    "name": child["name"],
                    "parent_id": parent_id,
                    "kind": child["kind"],
                    "color": child.get("color"),
                    "icon": child.get("icon"),
                },
            )

    await session.execute(
        text(
            "INSERT INTO accounts (id, user_id, name, type, currency, opening_balance, is_spendable) "
            "VALUES (:id, :uid, 'Cash', 'cash', 'INR', 0, TRUE)"
        ),
        {"id": str(uuid.uuid4()), "uid": user_id},
    )
