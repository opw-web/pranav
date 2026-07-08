
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.recurring import confirm_series, list_series, scan_and_upsert, upcoming
from app.templating import templates

router = APIRouter()


@router.get("/recurring")
async def recurring_page(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await scan_and_upsert(db, user.id)  # refresh detection on view
    series = await list_series(db, user.id)
    due = await upcoming(db, user.id)
    return templates.TemplateResponse(
        request, "recurring.html", {"detected": series["detected"], "active": series["active"], "upcoming": due}
    )


@router.post("/recurring/{series_id}/confirm")
async def confirm(
    request: Request,
    series_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await confirm_series(db, user.id, series_id)
    series = await list_series(db, user.id)
    due = await upcoming(db, user.id)
    return templates.TemplateResponse(
        request, "partials/recurring_lists.html",
        {"detected": series["detected"], "active": series["active"], "upcoming": due},
    )
