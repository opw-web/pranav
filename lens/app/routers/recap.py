from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.recap import get_recap

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/recap/{period}")
async def recap_page(
    request: Request,
    period: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    stats = await get_recap(db, user.id, period)
    return templates.TemplateResponse(request, "recap.html", {"stats": stats, "period": period})
