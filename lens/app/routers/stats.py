from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.stats import build_stats
from app.templating import templates

router = APIRouter()


@router.get("/stats")
async def stats_page(
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
        # First-run empty state — never a blank chart (dashboard.py precedent).
        return templates.TemplateResponse(request, "stats.html", {"empty": True})

    data = await build_stats(db, user.id)

    return templates.TemplateResponse(
        request,
        "stats.html",
        {"empty": False, "donut": data["donut"], "trend": data["trend"]},
    )
