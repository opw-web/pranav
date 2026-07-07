from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.routers.accounts import router as accounts_router
from app.routers.categories import router as categories_router
from app.routers.cron import router as cron_router
from app.routers.dashboard import router as dashboard_router
from app.routers.import_ import router as import_router
from app.routers.insights import router as insights_router
from app.routers.recap import router as recap_router
from app.routers.recurring import router as recurring_router
from app.routers.rules import router as rules_router
from app.routers.settings import router as settings_router
from app.routers.transactions import router as transactions_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="LENS")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(rules_router)
app.include_router(import_router)
app.include_router(recurring_router)
app.include_router(cron_router)
app.include_router(dashboard_router)
app.include_router(insights_router)
app.include_router(recap_router)
app.include_router(settings_router)


@app.exception_handler(HTTPException)
async def auth_redirect_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse("/login")
    return await http_exception_handler(request, exc)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
