import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.balances import get_account_balances, get_single_account_balance
from app.services.reconcile import reconcile_account

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/accounts")
async def list_accounts(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    accounts = await get_account_balances(db, user.id)
    return templates.TemplateResponse(request, "accounts.html", {"accounts": accounts, "user": user})


@router.post("/accounts")
async def create_account(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    currency: str = Form("INR"),
    opening_balance: float = Form(0),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    is_spendable = type != "credit_card"
    await db.execute(
        text(
            "INSERT INTO accounts (id, user_id, name, type, currency, opening_balance, is_spendable) "
            "VALUES (:id, :uid, :name, :type, :currency, :ob, :spendable)"
        ),
        {
            "id": str(uuid.uuid4()),
            "uid": user.id,
            "name": name,
            "type": type,
            "currency": currency,
            "ob": opening_balance,
            "spendable": is_spendable,
        },
    )
    accounts = await get_account_balances(db, user.id)
    return templates.TemplateResponse(request, "partials/account_list.html", {"accounts": accounts})


@router.patch("/accounts/{account_id}")
async def rename_account(
    request: Request,
    account_id: str,
    name: str = Form(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await db.execute(
        text("UPDATE accounts SET name = :name WHERE id = :aid AND user_id = :uid"),
        {"name": name, "aid": account_id, "uid": user.id},
    )
    row = await get_single_account_balance(db, user.id, account_id)
    return templates.TemplateResponse(request, "partials/account_row.html", {"a": row})


@router.post("/accounts/{account_id}/archive")
async def archive_account(
    request: Request,
    account_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await db.execute(
        text("UPDATE accounts SET is_archived = NOT is_archived WHERE id = :aid AND user_id = :uid"),
        {"aid": account_id, "uid": user.id},
    )
    accounts = await get_account_balances(db, user.id)
    return templates.TemplateResponse(request, "partials/account_list.html", {"accounts": accounts})


@router.post("/accounts/{account_id}/reconcile")
async def reconcile(
    request: Request,
    account_id: str,
    actual_balance: float = Form(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    result = await reconcile_account(db, user.id, account_id, actual_balance)
    row = await get_single_account_balance(db, user.id, account_id)
    return templates.TemplateResponse(
        request, "partials/account_row.html", {"a": row, "reconciled": result}
    )
