"""Scheduled jobs invoked by Vercel Cron (§4.3). Not user-facing: protected by a shared
secret and uses an admin DB session (crosses users) rather than an RLS-scoped one.
Wire the schedule in vercel.json (Task 13)."""

import os
from datetime import date, timedelta

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text

from app.database import async_session

router = APIRouter()

CRON_SECRET = os.environ.get("CRON_SECRET", "")


def _authorize(authorization: str | None):
    expected = f"Bearer {CRON_SECRET}"
    if not CRON_SECRET or authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/internal/cron/recurring-reminders")
async def recurring_reminders(authorization: str | None = Header(default=None)):
    """Find active series due within 3 days, and flag renewals that came in higher than
    the expected amount ('renewed higher than usual', §4.3). Returns a summary; actual
    delivery (email/push) plugs in here once a provider is configured."""
    _authorize(authorization)
    horizon = date.today() + timedelta(days=3)

    async with async_session() as db:
        due = (
            await db.execute(
                text(
                    "SELECT r.user_id, r.merchant_clean, r.next_due_date, r.expected_amount, r.amount_tolerance "
                    "FROM recurring_series r "
                    "WHERE r.status = 'active' AND r.next_due_date IS NOT NULL AND r.next_due_date <= :h"
                ),
                {"h": horizon},
            )
        ).mappings().all()

        # flag most-recent charge that exceeded expected * (1 + tolerance)
        higher = (
            await db.execute(
                text(
                    "SELECT r.user_id, r.merchant_clean, r.expected_amount, latest.amount AS latest_amount "
                    "FROM recurring_series r "
                    "JOIN LATERAL ("
                    "  SELECT amount FROM transactions t "
                    "  WHERE t.user_id = r.user_id AND t.merchant_clean = r.merchant_clean "
                    "    AND t.type = 'expense' AND t.is_deleted = FALSE "
                    "  ORDER BY t.txn_date DESC LIMIT 1"
                    ") latest ON true "
                    "WHERE r.status = 'active' AND r.expected_amount IS NOT NULL "
                    "  AND latest.amount > r.expected_amount * (1 + r.amount_tolerance)"
                )
            )
        ).mappings().all()

    return {
        "due_soon": [dict(d) for d in due],
        "renewed_higher": [dict(h) for h in higher],
        "counts": {"due_soon": len(due), "renewed_higher": len(higher)},
    }
