"""Savings recommendation (§WS6) — income minus typical essential + discretionary spend.

Reuses category_normals() and the essential-category set from analytics.py so the
numbers match safe-to-spend's view of "essential". No new categorization logic.
"""

from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics import _essential_category_ids, category_normals


async def get_user_settings(session: AsyncSession, user_id: str) -> dict:
    row = (
        await session.execute(
            text(
                "SELECT monthly_income, savings_goal FROM user_settings WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
    ).mappings().first()
    if not row:
        return {"monthly_income": None, "savings_goal": None}
    return {
        "monthly_income": float(row["monthly_income"]) if row["monthly_income"] is not None else None,
        "savings_goal": float(row["savings_goal"]) if row["savings_goal"] is not None else None,
    }


async def save_user_settings(
    session: AsyncSession,
    user_id: str,
    monthly_income: float | None,
    savings_goal: float | None = None,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO user_settings (user_id, monthly_income, savings_goal, updated_at)
            VALUES (:uid, :income, :goal, now())
            ON CONFLICT (user_id) DO UPDATE SET
                monthly_income = EXCLUDED.monthly_income,
                savings_goal = EXCLUDED.savings_goal,
                updated_at = now()
            """
        ),
        {"uid": user_id, "income": monthly_income, "goal": savings_goal},
    )


def _guidance(
    income: float,
    essential_normal: float,
    discretionary_normal: float,
    recommended: float,
    savings_goal: float | None,
) -> str:
    typical_spend = essential_normal + discretionary_normal
    if typical_spend <= 0:
        return (
            f"Based on your income of ₹{income:,.0f} — add a few transactions "
            "so we can estimate your typical spending."
        )
    if recommended >= 0:
        msg = (
            f"You typically spend ₹{essential_normal:,.0f} on essentials and "
            f"₹{discretionary_normal:,.0f} on everything else. "
            f"Setting aside ₹{recommended:,.0f} each month leaves room for savings."
        )
    else:
        msg = (
            f"Your typical spending (₹{typical_spend:,.0f}) exceeds your income "
            f"(₹{income:,.0f}) — review discretionary categories or adjust income."
        )
    if savings_goal is not None and recommended >= 0:
        gap = round(recommended - savings_goal, 2)
        if gap >= 0:
            msg += f" That covers your ₹{savings_goal:,.0f} savings goal with ₹{gap:,.0f} to spare."
        else:
            msg += f" Your ₹{savings_goal:,.0f} goal is ₹{abs(gap):,.0f} above what typical spending allows."
    return msg


def compute_recommended(
    income: float,
    essential_normal: float,
    discretionary_normal: float,
    savings_goal: float | None = None,
) -> dict:
    """Pure math + guidance — testable without a DB."""
    recommended = round(income - essential_normal - discretionary_normal, 2)
    return {
        "has_income": True,
        "monthly_income": round(income, 2),
        "essential_normal": round(essential_normal, 2),
        "discretionary_normal": round(discretionary_normal, 2),
        "recommended": recommended,
        "savings_goal": savings_goal,
        "guidance": _guidance(income, essential_normal, discretionary_normal, recommended, savings_goal),
    }


async def savings_recommendation(
    session: AsyncSession, user_id: str, ref: date | None = None
) -> dict:
    settings = await get_user_settings(session, user_id)
    income = settings.get("monthly_income")
    goal = settings.get("savings_goal")

    if income is None:
        return {
            "has_income": False,
            "monthly_income": None,
            "savings_goal": goal,
            "recommended": None,
            "essential_normal": None,
            "discretionary_normal": None,
            "guidance": "Set your monthly income in Settings to get a savings recommendation.",
        }

    normals = await category_normals(session, user_id, ref)
    essential_ids = await _essential_category_ids(session, user_id)
    essential_normal = sum(normals.get(cid, 0.0) for cid in essential_ids)
    discretionary_normal = sum(v for cid, v in normals.items() if cid not in essential_ids)

    result = compute_recommended(income, essential_normal, discretionary_normal, goal)
    result["savings_goal"] = goal
    return result
