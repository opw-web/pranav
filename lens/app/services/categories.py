"""Category tree, fuzzy picker search, and create/rename/merge — reused by the
manage page (Task 5), and later by the categorizer + quick-add parser which also
need to resolve category names (Task 7/8)."""

import uuid

from rapidfuzz import fuzz
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

PALETTE = [
    "#F59E0B", "#3B82F6", "#EC4899", "#8B5CF6",
    "#10B981", "#06B6D4", "#EF4444", "#22C55E",
    "#F97316", "#6366F1",
]
DEFAULT_ICON = "🏷️"

_USAGE_SQL = """
WITH usage AS (
    SELECT category_id, count(*) AS cnt, max(updated_at) AS last_used
    FROM transactions
    WHERE user_id = :uid AND is_deleted = FALSE AND category_id IS NOT NULL
    GROUP BY category_id
)
SELECT c.id, c.name, c.parent_id, c.kind, c.color, c.icon, c.is_system,
       COALESCE(u.cnt, 0) AS usage_count, u.last_used
FROM categories c
LEFT JOIN usage u ON u.category_id = c.id
WHERE c.user_id = :uid
ORDER BY c.sort_order, c.name
"""


class MaxDepthError(ValueError):
    pass


_KEYWORDS_SQL = """
SELECT id, pattern, set_category_id AS category_id
FROM categorization_rules
WHERE user_id = :uid AND match_type = 'contains' AND set_category_id IS NOT NULL
ORDER BY pattern
"""


async def _all_categories_with_usage(session: AsyncSession, user_id: str):
    result = await session.execute(text(_USAGE_SQL), {"uid": user_id})
    return result.mappings().all()


async def get_grouped_tree(session: AsyncSession, user_id: str):
    """Default (no-query) picker view: top-level groups ranked by their own +
    children's usage, each with children ranked by their own usage. Satisfies
    'recent & frequent on top' + 'parents with indented children' (§5.2).

    Each node also carries its reason `keywords` (§WS4a) - fetched in one extra
    query here so every caller (the category management page, quick-add, the
    seed-key resolver) sees the same shape without an N+1 per category."""
    rows = await _all_categories_with_usage(session, user_id)
    by_id = {row["id"]: dict(row, children=[], keywords=[]) for row in rows}

    kw_rows = await session.execute(text(_KEYWORDS_SQL), {"uid": user_id})
    for kw in kw_rows.mappings().all():
        node = by_id.get(kw["category_id"])
        if node is not None:
            node["keywords"].append({"id": kw["id"], "pattern": kw["pattern"]})

    top_level = []
    for row in rows:
        node = by_id[row["id"]]
        if row["parent_id"] is None:
            top_level.append(node)
        else:
            parent = by_id.get(row["parent_id"])
            if parent is not None:
                parent["children"].append(node)

    for node in top_level:
        node["is_child"] = False
        for child in node["children"]:
            child["is_child"] = True
        node["children"].sort(key=lambda c: (-c["usage_count"], c["name"]))
        node["group_score"] = node["usage_count"] + sum(c["usage_count"] for c in node["children"])

    top_level.sort(key=lambda n: (-n["group_score"], n["name"]))
    return top_level


async def fuzzy_search(session: AsyncSession, user_id: str, query: str, limit: int = 20):
    """Flat, ranked results across the whole tree for a non-empty query (§5.2)."""
    rows = await _all_categories_with_usage(session, user_id)
    by_id = {row["id"]: row for row in rows}

    scored = []
    for row in rows:
        parent = by_id.get(row["parent_id"]) if row["parent_id"] else None
        label = f"{parent['name']} › {row['name']}" if parent else row["name"]
        score = fuzz.WRatio(query, label)
        scored.append((score, dict(row, label=label, is_child=parent is not None)))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    results = [item for score, item in scored[:limit] if score > 40]

    exact_match = any(r["name"].lower() == query.strip().lower() for r in rows)
    return results, exact_match


def keyword_matches(pattern: str, query: str) -> bool:
    """A reason keyword 'matches' a picker query if the (lowercased, stripped) query
    is a substring of the keyword pattern - e.g. query 'fu' matches pattern 'fuel'.
    Pure so the picker's match rule is independently testable without a DB."""
    q = query.strip().lower()
    return bool(q) and q in pattern.lower()


async def search_with_keywords(session: AsyncSession, user_id: str, query: str, limit: int = 20):
    """Picker search (§WS4a): the existing name-based fuzzy_search, plus any
    category whose reason keyword matches the query as a substring (case-
    insensitive - typing "fu" surfaces a category keyworded "fuel"). Keyword hits
    are de-duplicated against the name results and tagged with `matched_keyword`
    so the picker can show why they showed up. Returns (results, keyword_hits, exact_match)."""
    results, exact_match = await fuzzy_search(session, user_id, query, limit=limit)
    seen_ids = {str(row["id"]) for row in results}

    q = query.strip().lower()
    keyword_hits = []
    if q:
        rows = await _all_categories_with_usage(session, user_id)
        by_id = {row["id"]: row for row in rows}
        kw_rows = (
            await session.execute(text(_KEYWORDS_SQL), {"uid": user_id})
        ).mappings().all()
        for kw in kw_rows:
            category_id = kw["category_id"]
            if category_id is None or str(category_id) in seen_ids or not keyword_matches(kw["pattern"], q):
                continue
            cat = by_id.get(category_id)
            if cat is None:
                continue
            parent = by_id.get(cat["parent_id"]) if cat["parent_id"] else None
            label = f"{parent['name']} › {cat['name']}" if parent else cat["name"]
            keyword_hits.append(
                dict(cat, label=label, is_child=parent is not None, matched_keyword=kw["pattern"])
            )
            seen_ids.add(str(category_id))

    return results, keyword_hits, exact_match


async def create_category(
    session: AsyncSession,
    user_id: str,
    name: str,
    parent_id: str | None = None,
    kind: str = "expense",
    color: str | None = None,
    icon: str | None = None,
) -> dict:
    name = name.strip()
    if not name:
        raise ValueError("Category name cannot be empty")

    if parent_id:
        parent = (
            await session.execute(
                text("SELECT parent_id FROM categories WHERE id = :pid AND user_id = :uid"),
                {"pid": parent_id, "uid": user_id},
            )
        ).mappings().first()
        if parent is None:
            raise ValueError("Parent category not found")
        if parent["parent_id"] is not None:
            raise MaxDepthError("Categories can only be 2 levels deep")

    if color is None:
        existing_count = (
            await session.execute(text("SELECT count(*) FROM categories WHERE user_id = :uid"), {"uid": user_id})
        ).scalar()
        color = PALETTE[existing_count % len(PALETTE)]
    icon = icon or DEFAULT_ICON

    new_id = str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO categories (id, user_id, name, parent_id, kind, color, icon, is_system) "
            "VALUES (:id, :uid, :name, :parent_id, :kind, :color, :icon, FALSE)"
        ),
        {"id": new_id, "uid": user_id, "name": name, "parent_id": parent_id, "kind": kind, "color": color, "icon": icon},
    )
    return {"id": new_id, "name": name, "parent_id": parent_id, "kind": kind, "color": color, "icon": icon}


async def rename_category(session: AsyncSession, user_id: str, category_id: str, new_name: str):
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Category name cannot be empty")
    await session.execute(
        text("UPDATE categories SET name = :name WHERE id = :cid AND user_id = :uid"),
        {"name": new_name, "cid": category_id, "uid": user_id},
    )


async def merge_categories(session: AsyncSession, user_id: str, source_id: str, target_id: str):
    """Reassign all of source's transactions (and children) to target, then delete source.
    History stays intact (§5.2 'Merge & rename without data loss')."""
    if source_id == target_id:
        raise ValueError("Cannot merge a category into itself")

    await session.execute(
        text("UPDATE transactions SET category_id = :target WHERE category_id = :source AND user_id = :uid"),
        {"target": target_id, "source": source_id, "uid": user_id},
    )
    await session.execute(
        text("UPDATE categories SET parent_id = :target WHERE parent_id = :source AND user_id = :uid"),
        {"target": target_id, "source": source_id, "uid": user_id},
    )
    await session.execute(
        text("DELETE FROM categories WHERE id = :source AND user_id = :uid"),
        {"source": source_id, "uid": user_id},
    )


async def delete_category(session: AsyncSession, user_id: str, category_id: str):
    await session.execute(
        text("DELETE FROM categories WHERE id = :cid AND user_id = :uid"),
        {"cid": category_id, "uid": user_id},
    )
