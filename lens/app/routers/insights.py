from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.analytics import spending_detective, trip_rollup, what_changed

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/insights")
async def insights_page(
    request: Request,
    tag: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    detective = await spending_detective(db, user.id)
    diff = await what_changed(db, user.id)

    tags = [
        r[0]
        for r in (
            await db.execute(text("SELECT name FROM tags WHERE user_id=:uid ORDER BY name"), {"uid": user.id})
        ).all()
    ]
    rollup = await trip_rollup(db, user.id, tag) if tag else None

    return templates.TemplateResponse(
        request,
        "insights.html",
        {"detective": detective, "diff": diff, "tags": tags, "rollup": rollup, "selected_tag": tag},
    )
