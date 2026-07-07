"""Monthly recap builder (§4.4/§5). Template + numbers, cached in monthly_recaps so a
past month is computed once. Current (incomplete) month is always recomputed live."""

import json
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics import month_bounds, spending_detective


def _period_bounds(period: str) -> tuple[date, date]:
    year, month = (int(x) for x in period.split("-"))
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


async def build_recap(session: AsyncSession, user_id: str, period: str) -> dict:
    """period = 'YYYY-MM'. Returns totals + top categories + Detective headline for that month."""
    start, end = _period_bounds(period)

    totals = (
        await session.execute(
            text(
                "SELECT "
                "COALESCE(SUM(amount) FILTER (WHERE type='expense'),0) AS expense, "
                "COALESCE(SUM(amount) FILTER (WHERE type='income'),0) AS income, "
                "COALESCE(SUM(amount) FILTER (WHERE type='refund'),0) AS refund, "
                "COUNT(*) FILTER (WHERE type='expense') AS expense_count "
                "FROM transactions WHERE user_id=:uid AND is_deleted=FALSE "
                "AND txn_date>=:s AND txn_date<:e"
            ),
            {"uid": user_id, "s": start, "e": end},
        )
    ).mappings().first()

    top_categories = [
        {"category": r["name"] or "Uncategorized", "total": round(float(r["total"]), 2)}
        for r in (
            await session.execute(
                text(
                    "SELECT c.name, SUM(t.amount) AS total FROM transactions t "
                    "LEFT JOIN categories c ON c.id=t.category_id "
                    "WHERE t.user_id=:uid AND t.type='expense' AND t.is_deleted=FALSE "
                    "AND t.txn_date>=:s AND t.txn_date<:e GROUP BY c.name ORDER BY total DESC LIMIT 5"
                ),
                {"uid": user_id, "s": start, "e": end},
            )
        ).mappings().all()
    ]

    detective = await spending_detective(session, user_id, ref=start)

    return {
        "period": period,
        "expense": round(float(totals["expense"]), 2),
        "income": round(float(totals["income"]), 2),
        "refund": round(float(totals["refund"]), 2),
        "net": round(float(totals["income"]) + float(totals["refund"]) - float(totals["expense"]), 2),
        "expense_count": totals["expense_count"],
        "top_categories": top_categories,
        "headline": detective["headline"],
    }


async def get_recap(session: AsyncSession, user_id: str, period: str) -> dict:
    """Cache read-through. Past months cached in monthly_recaps; current month always fresh."""
    cur_period = date.today().strftime("%Y-%m")
    if period != cur_period:
        cached = (
            await session.execute(
                text("SELECT stats FROM monthly_recaps WHERE user_id=:uid AND period=:p"),
                {"uid": user_id, "p": period},
            )
        ).scalar()
        if cached:
            return cached if isinstance(cached, dict) else json.loads(cached)

    stats = await build_recap(session, user_id, period)

    if period != cur_period:
        await session.execute(
            text(
                "INSERT INTO monthly_recaps (user_id, period, stats) VALUES (:uid,:p,CAST(:s AS JSONB)) "
                "ON CONFLICT (user_id, period) DO UPDATE SET stats=EXCLUDED.stats"
            ),
            {"uid": user_id, "p": period, "s": json.dumps(stats)},
        )
    return stats
