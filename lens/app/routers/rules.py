from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.categorizer import back_apply_rule, learn_rule

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


async def _rules_with_names(db: AsyncSession, user_id: str):
    return (
        await db.execute(
            text(
                "SELECT r.id, r.match_type, r.pattern, r.set_merchant, r.priority, r.times_applied, "
                "       c.name AS category_name, c.icon AS category_icon "
                "FROM categorization_rules r "
                "LEFT JOIN categories c ON c.id = r.set_category_id "
                "WHERE r.user_id = :uid ORDER BY r.priority ASC, r.created_at DESC"
            ),
            {"uid": user_id},
        )
    ).mappings().all()


@router.get("/rules")
async def rules_page(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    rules = await _rules_with_names(db, user.id)
    return templates.TemplateResponse(request, "rules.html", {"rules": rules})


@router.post("/rules/learn")
async def learn(
    request: Request,
    txn_id: str = Form(...),
    category_id: str | None = Form(None),
    back_apply: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    """Called when the user accepts 'Always categorize <merchant> as <category>?'.
    Creates a rule from the transaction's merchant_raw and, if asked, back-applies
    it to existing uncategorized matches."""
    row = (
        await db.execute(
            text("SELECT merchant_raw, merchant_clean FROM transactions WHERE id = :tid AND user_id = :uid"),
            {"tid": txn_id, "uid": user.id},
        )
    ).mappings().first()
    if row is None or not (row["merchant_raw"] or row["merchant_clean"]):
        return templates.TemplateResponse(
            request, "partials/toast.html", {"message": "Nothing to learn from.", "kind": "error"}
        )

    source = row["merchant_raw"] or row["merchant_clean"]
    category_id = category_id or None
    learned = await learn_rule(db, user.id, source, category_id, set_merchant=row["merchant_clean"])

    applied = 0
    if back_apply == "on" and category_id:
        applied = await back_apply_rule(db, user.id, learned["pattern"], category_id)

    msg = f"Rule saved for “{learned['pattern']}”."
    if applied:
        msg += f" Applied to {applied} existing transaction{'s' if applied != 1 else ''}."
    return templates.TemplateResponse(request, "partials/toast.html", {"message": msg})


@router.delete("/rules/{rule_id}")
async def delete_rule(
    request: Request,
    rule_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await db.execute(
        text("DELETE FROM categorization_rules WHERE id = :rid AND user_id = :uid"),
        {"rid": rule_id, "uid": user.id},
    )
    rules = await _rules_with_names(db, user.id)
    return templates.TemplateResponse(request, "partials/rules_table.html", {"rules": rules})
