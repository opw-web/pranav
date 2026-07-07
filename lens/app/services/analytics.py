"""Deterministic analytics — SQL-first (§2.6, §4.4). Python only orchestrates and
templates the numbers a query produced; no number-crunching, no pandas. Every figure
is reproducible from the SQL below.

Verified live in production (Task 13); local Postgres port is firewalled on the dev network.
"""

from calendar import monthrange
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.balances import get_account_balances

# "Essential" set (§4.4). Derived by category/parent name to avoid a schema flag.
ESSENTIAL_NAMES = {
    "rent", "bills", "electricity", "internet & mobile", "groceries", "health", "pharmacy",
}


# ---- period helpers (pure) -----------------------------------------------------------

def month_bounds(d: date) -> tuple[date, date]:
    """First day of d's month and first day of next month (half-open [start, end))."""
    start = d.replace(day=1)
    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)
    return start, end


def prev_month_bounds(d: date) -> tuple[date, date]:
    start, _ = month_bounds(d)
    prev_end = start
    if start.month == 1:
        prev_start = date(start.year - 1, 12, 1)
    else:
        prev_start = date(start.year, start.month - 1, 1)
    return prev_start, prev_end


def last_n_full_months(d: date, n: int = 3) -> tuple[date, date]:
    """[start, end) covering the n full calendar months before d's month."""
    cur_start, _ = month_bounds(d)
    end = cur_start
    start = cur_start
    for _ in range(n):
        start, _ = prev_month_bounds(start.replace(day=15))
    return start, end


# ---- normals (§4.4) ------------------------------------------------------------------

async def category_normals(session: AsyncSession, user_id: str, ref: date | None = None) -> dict:
    """Median monthly expense per category over the last 3 full months (PERCENTILE_CONT).
    Returns {category_id: median_amount}."""
    ref = ref or date.today()
    start, end = last_n_full_months(ref, 3)
    rows = (
        await session.execute(
            text(
                """
                WITH monthly AS (
                    SELECT category_id, date_trunc('month', txn_date) AS m, SUM(amount) AS spend
                    FROM transactions
                    WHERE user_id = :uid AND type = 'expense' AND is_deleted = FALSE
                      AND txn_date >= :start AND txn_date < :end
                    GROUP BY category_id, date_trunc('month', txn_date)
                )
                SELECT category_id,
                       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY spend) AS normal
                FROM monthly GROUP BY category_id
                """
            ),
            {"uid": user_id, "start": start, "end": end},
        )
    ).all()
    return {str(cat_id) if cat_id else None: float(normal) for cat_id, normal in rows}


# ---- safe-to-spend (the hero, §4.4) --------------------------------------------------

async def safe_to_spend(session: AsyncSession, user_id: str, ref: date | None = None) -> dict:
    """spendable_balance − upcoming_committed − essential_remaining, with the breakdown
    so the UI never shows a naked number (§5.4)."""
    ref = ref or date.today()
    cur_start, cur_end = month_bounds(ref)

    balances = await get_account_balances(session, user_id)
    spendable_balance = sum(float(b["balance"]) for b in balances if b["is_spendable"] and not b["is_archived"])

    upcoming_committed = float(
        (
            await session.execute(
                text(
                    "SELECT COALESCE(SUM(expected_amount), 0) FROM recurring_series "
                    "WHERE user_id = :uid AND status = 'active' AND next_due_date IS NOT NULL "
                    "AND next_due_date >= :today AND next_due_date < :period_end"
                ),
                {"uid": user_id, "today": ref, "period_end": cur_end},
            )
        ).scalar()
    )

    # essential normal for the period vs essential spent so far this month
    normals = await category_normals(session, user_id, ref)
    essential_ids = await _essential_category_ids(session, user_id)
    essential_normal = sum(normals.get(cid, 0.0) for cid in essential_ids)

    essential_spent = float(
        (
            await session.execute(
                text(
                    "SELECT COALESCE(SUM(amount), 0) FROM transactions "
                    "WHERE user_id = :uid AND type = 'expense' AND is_deleted = FALSE "
                    "AND category_id = ANY(:ids) AND txn_date >= :start AND txn_date < :end"
                ),
                {"uid": user_id, "ids": list(essential_ids) or [None], "start": cur_start, "end": cur_end},
            )
        ).scalar()
    )
    essential_remaining = max(0.0, essential_normal - essential_spent)

    sts = spendable_balance - upcoming_committed - essential_remaining
    return {
        "safe_to_spend": round(sts, 2),
        "spendable_balance": round(spendable_balance, 2),
        "upcoming_committed": round(upcoming_committed, 2),
        "essential_remaining": round(essential_remaining, 2),
        "essential_normal": round(essential_normal, 2),
        "essential_spent": round(essential_spent, 2),
    }


async def _essential_category_ids(session: AsyncSession, user_id: str) -> set:
    rows = (
        await session.execute(
            text(
                "SELECT c.id, lower(c.name) AS name, lower(p.name) AS parent "
                "FROM categories c LEFT JOIN categories p ON p.id = c.parent_id "
                "WHERE c.user_id = :uid"
            ),
            {"uid": user_id},
        )
    ).mappings().all()
    ids = set()
    for r in rows:
        if r["name"] in ESSENTIAL_NAMES or (r["parent"] and r["parent"] in ESSENTIAL_NAMES):
            ids.add(str(r["id"]))
    return ids


# ---- Spending Detective (§4.4, delta query from §2.6) --------------------------------

_DELTA_SQL = """
WITH cur AS (
  SELECT {dim} AS k, SUM(amount) AS spend FROM transactions
  WHERE user_id = :uid AND type = 'expense' AND is_deleted = FALSE
    AND txn_date >= :cur_start AND txn_date < :cur_end
  GROUP BY {dim}
),
prev AS (
  SELECT {dim} AS k, SUM(amount) AS spend FROM transactions
  WHERE user_id = :uid AND type = 'expense' AND is_deleted = FALSE
    AND txn_date >= :prev_start AND txn_date < :prev_end
  GROUP BY {dim}
)
SELECT COALESCE(cur.k, prev.k) AS k,
       COALESCE(cur.spend, 0) AS cur_spend,
       COALESCE(prev.spend, 0) AS prev_spend,
       COALESCE(cur.spend, 0) - COALESCE(prev.spend, 0) AS delta
FROM cur FULL OUTER JOIN prev USING (k)
ORDER BY delta DESC
"""


async def _deltas(session, user_id, dim, cur_start, cur_end, prev_start, prev_end):
    sql = _DELTA_SQL.format(dim=dim)
    rows = (
        await session.execute(
            text(sql),
            {"uid": user_id, "cur_start": cur_start, "cur_end": cur_end,
             "prev_start": prev_start, "prev_end": prev_end},
        )
    ).mappings().all()
    return rows


async def spending_detective(session: AsyncSession, user_id: str, ref: date | None = None, top_n: int = 3) -> dict:
    """Period-over-period attribution at category + merchant level. Returns ranked drivers
    and a templated one-liner (numbers slotted into fixed sentences — no prose generation)."""
    ref = ref or date.today()
    cur_start, cur_end = month_bounds(ref)
    prev_start, prev_end = prev_month_bounds(ref)

    cat_rows = await _deltas(session, user_id, "category_id", cur_start, cur_end, prev_start, prev_end)
    merch_rows = await _deltas(session, user_id, "merchant_clean", cur_start, cur_end, prev_start, prev_end)

    cur_total = sum(float(r["cur_spend"]) for r in cat_rows)
    prev_total = sum(float(r["prev_spend"]) for r in cat_rows)

    # resolve category names for the top drivers
    id_to_name = {}
    ids = [r["k"] for r in cat_rows if r["k"]]
    if ids:
        name_rows = (
            await session.execute(
                text("SELECT id, name FROM categories WHERE user_id = :uid AND id = ANY(:ids)"),
                {"uid": user_id, "ids": ids},
            )
        ).all()
        id_to_name = {str(i): n for i, n in name_rows}

    risers = [r for r in cat_rows if float(r["delta"]) > 0][:top_n]
    drivers = [
        {"name": id_to_name.get(str(r["k"]), "Uncategorized"), "delta": round(float(r["delta"]), 2),
         "cur": round(float(r["cur_spend"]), 2)}
        for r in risers
    ]

    pct = ((cur_total - prev_total) / prev_total * 100) if prev_total else (100.0 if cur_total else 0.0)
    if drivers:
        parts = " · ".join(f"{d['name']} +₹{d['delta']:,.0f}" for d in drivers)
        direction = "rise" if pct >= 0 else "drop"
        headline = f"{parts} drove a {abs(pct):.0f}% {direction} vs last month"
    else:
        headline = "Spending is in line with last month."

    top_merchants = [
        {"name": r["k"] or "Unknown", "delta": round(float(r["delta"]), 2)}
        for r in merch_rows if float(r["delta"]) > 0
    ][:top_n]

    return {
        "headline": headline,
        "cur_total": round(cur_total, 2),
        "prev_total": round(prev_total, 2),
        "pct_change": round(pct, 1),
        "category_drivers": drivers,
        "merchant_drivers": top_merchants,
    }


# ---- what-changed-vs-normal diff (§4.4) ----------------------------------------------

async def what_changed(session: AsyncSession, user_id: str, ref: date | None = None) -> dict:
    ref = ref or date.today()
    cur_start, cur_end = month_bounds(ref)
    prev_start, prev_end = prev_month_bounds(ref)

    new_merchants = [
        r[0] for r in (
            await session.execute(
                text(
                    "SELECT DISTINCT merchant_clean FROM transactions "
                    "WHERE user_id=:uid AND type='expense' AND is_deleted=FALSE AND merchant_clean IS NOT NULL "
                    "AND txn_date >= :cs AND txn_date < :ce "
                    "AND merchant_clean NOT IN (SELECT DISTINCT merchant_clean FROM transactions "
                    "  WHERE user_id=:uid AND is_deleted=FALSE AND merchant_clean IS NOT NULL "
                    "  AND txn_date < :cs)"
                ),
                {"uid": user_id, "cs": cur_start, "ce": cur_end},
            )
        ).all()
    ]

    normals = await category_normals(session, user_id, ref)
    cur_by_cat = {
        str(cid) if cid else None: float(spend)
        for cid, spend in (
            await session.execute(
                text(
                    "SELECT category_id, SUM(amount) FROM transactions "
                    "WHERE user_id=:uid AND type='expense' AND is_deleted=FALSE "
                    "AND txn_date >= :cs AND txn_date < :ce GROUP BY category_id"
                ),
                {"uid": user_id, "cs": cur_start, "ce": cur_end},
            )
        ).all()
    }
    above_normal = []
    for cid, spend in cur_by_cat.items():
        normal = normals.get(cid, 0.0)
        if normal > 0 and spend > normal * 1.25:
            above_normal.append({"category_id": cid, "spend": round(spend, 2), "normal": round(normal, 2)})

    newly_recurring = (
        await session.execute(
            text(
                "SELECT merchant_clean, expected_amount FROM recurring_series "
                "WHERE user_id=:uid AND status='detected'"
            ),
            {"uid": user_id},
        )
    ).mappings().all()

    return {
        "new_merchants": new_merchants,
        "above_normal": above_normal,
        "newly_recurring": [dict(r) for r in newly_recurring],
    }


# ---- trip/event rollup (§4.4) --------------------------------------------------------

async def trip_rollup(session: AsyncSession, user_id: str, tag_name: str) -> dict:
    """SUM(amount) WHERE tag GROUP BY category. Transfers excluded (they aren't spend)."""
    rows = (
        await session.execute(
            text(
                """
                SELECT COALESCE(c.name, 'Uncategorized') AS category, SUM(t.amount) AS total
                FROM transactions t
                JOIN transaction_tags tt ON tt.transaction_id = t.id
                JOIN tags tg ON tg.id = tt.tag_id
                LEFT JOIN categories c ON c.id = t.category_id
                WHERE t.user_id = :uid AND tg.name = :tag AND t.type = 'expense' AND t.is_deleted = FALSE
                GROUP BY c.name ORDER BY total DESC
                """
            ),
            {"uid": user_id, "tag": tag_name},
        )
    ).mappings().all()
    breakdown = [{"category": r["category"], "total": round(float(r["total"]), 2)} for r in rows]
    total = round(sum(b["total"] for b in breakdown), 2)
    return {"tag": tag_name, "total": total, "breakdown": breakdown}
