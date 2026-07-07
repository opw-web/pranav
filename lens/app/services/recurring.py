"""DB-facing recurring-series operations: scan history -> upsert detected series,
confirm (activate), list detected/active/upcoming. Detection math lives in
recurring_detector.py (pure)."""

import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.recurring_detector import detect_all


async def scan_and_upsert(session: AsyncSession, user_id: str) -> int:
    """Group the user's expense history by merchant_clean, detect series, and upsert
    any new ones as status='detected'. Returns count of newly detected series."""
    rows = (
        await session.execute(
            text(
                "SELECT merchant_clean, txn_date, amount FROM transactions "
                "WHERE user_id = :uid AND type = 'expense' AND is_deleted = FALSE "
                "AND merchant_clean IS NOT NULL"
            ),
            {"uid": user_id},
        )
    ).all()

    grouped: dict[str, list[tuple[date, float]]] = {}
    for merchant, txn_date, amount in rows:
        grouped.setdefault(merchant, []).append((txn_date, float(amount)))

    detected = detect_all(grouped)
    new_count = 0
    for s in detected:
        exists = (
            await session.execute(
                text(
                    "SELECT id FROM recurring_series WHERE user_id = :uid AND merchant_clean = :m"
                ),
                {"uid": user_id, "m": s.merchant_clean},
            )
        ).first()
        if exists:
            # refresh dates/amount but never downgrade an active series back to detected
            await session.execute(
                text(
                    "UPDATE recurring_series SET expected_amount = :amt, last_seen_date = :last, "
                    "next_due_date = :due, cadence = :cad WHERE user_id = :uid AND merchant_clean = :m"
                ),
                {"amt": s.expected_amount, "last": s.last_seen_date, "due": s.next_due_date,
                 "cad": s.cadence, "uid": user_id, "m": s.merchant_clean},
            )
        else:
            await session.execute(
                text(
                    "INSERT INTO recurring_series "
                    "(id, user_id, merchant_clean, expected_amount, cadence, next_due_date, last_seen_date, status) "
                    "VALUES (:id,:uid,:m,:amt,:cad,:due,:last,'detected')"
                ),
                {"id": str(uuid.uuid4()), "uid": user_id, "m": s.merchant_clean, "amt": s.expected_amount,
                 "cad": s.cadence, "due": s.next_due_date, "last": s.last_seen_date},
            )
            new_count += 1
    return new_count


async def list_series(session: AsyncSession, user_id: str):
    detected = (
        await session.execute(
            text(
                "SELECT * FROM recurring_series WHERE user_id = :uid AND status = 'detected' "
                "ORDER BY next_due_date"
            ),
            {"uid": user_id},
        )
    ).mappings().all()
    active = (
        await session.execute(
            text(
                "SELECT * FROM recurring_series WHERE user_id = :uid AND status = 'active' "
                "ORDER BY next_due_date"
            ),
            {"uid": user_id},
        )
    ).mappings().all()
    return {"detected": detected, "active": active}


async def confirm_series(session: AsyncSession, user_id: str, series_id: str):
    """Activate a detected series; recompute next_due_date from last_seen + cadence (§4.3)."""
    row = (
        await session.execute(
            text("SELECT cadence, last_seen_date FROM recurring_series WHERE id=:sid AND user_id=:uid"),
            {"sid": series_id, "uid": user_id},
        )
    ).mappings().first()
    if row is None:
        return
    days = {"weekly": 7, "monthly": 30, "yearly": 365}.get(row["cadence"], 30)
    next_due = (row["last_seen_date"] or date.today()) + timedelta(days=days)
    await session.execute(
        text(
            "UPDATE recurring_series SET status='active', next_due_date=:due WHERE id=:sid AND user_id=:uid"
        ),
        {"due": next_due, "sid": series_id, "uid": user_id},
    )


async def upcoming(session: AsyncSession, user_id: str, within_days: int = 30):
    """Active series due between today and today+within_days — feeds the dashboard and cron."""
    return (
        await session.execute(
            text(
                "SELECT * FROM recurring_series WHERE user_id = :uid AND status = 'active' "
                "AND next_due_date IS NOT NULL AND next_due_date <= :horizon ORDER BY next_due_date"
            ),
            {"uid": user_id, "horizon": date.today() + timedelta(days=within_days)},
        )
    ).mappings().all()
