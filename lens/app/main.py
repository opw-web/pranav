from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth.deps import CurrentUser, get_current_user
from app.auth.routes import router as auth_router
from app.routers.accounts import router as accounts_router
from app.routers.categories import router as categories_router
from app.routers.rules import router as rules_router
from app.routers.transactions import router as transactions_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="LENS")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(rules_router)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.exception_handler(HTTPException)
async def auth_redirect_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse("/login")
    return await http_exception_handler(request, exc)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/")
async def root(request: Request, user: CurrentUser = Depends(get_current_user)):
    return templates.TemplateResponse(request, "base.html", {"user": user})
