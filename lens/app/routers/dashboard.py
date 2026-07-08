
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.analytics import safe_to_spend, spending_detective
from app.services.recurring import upcoming
from app.services.transactions import list_transactions
from app.templating import templates

router = APIRouter()


@router.get("/")
async def dashboard(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    txn_count = (
        await db.execute(
            text("SELECT COUNT(*) FROM transactions WHERE user_id=:uid AND is_deleted=FALSE"),
            {"uid": user.id},
        )
    ).scalar()

    if not txn_count:
        # First-run empty state — never a blank grid (§4.6, Check 17)
        return templates.TemplateResponse(request, "dashboard.html", {"empty": True, "user": user})

    sts = await safe_to_spend(db, user.id)
    detective = await spending_detective(db, user.id)
    due = await upcoming(db, user.id, within_days=14)
    recent = await list_transactions(db, user.id, {}, limit=8)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"empty": False, "user": user, "sts": sts, "detective": detective, "upcoming": due, "recent": recent},
    )
