from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.balances import get_account_balances
from app.services.categories import get_grouped_tree
from app.services.quickadd import build_quickadd_preview
from app.services.tags import set_transaction_tags
from app.services.transactions import (
    bulk_delete,
    bulk_set_category,
    create_transaction,
    get_transaction,
    list_transactions,
    restore_transaction,
    soft_delete_transaction,
    update_transaction,
)
from app.templating import templates

router = APIRouter()


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


async def _flat_categories(db: AsyncSession, user_id: str):
    tree = await get_grouped_tree(db, user_id)
    flat = []
    for g in tree:
        flat.append({"id": g["id"], "label": g["name"]})
        for child in g["children"]:
            flat.append({"id": child["id"], "label": f"{g['name']} › {child['name']}"})
    return flat


@router.get("/txn")
async def list_txn_page(
    request: Request,
    account_id: str | None = None,
    category_id: str | None = None,
    type: str | None = None,
    uncategorized: bool = False,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    filters = {
        "account_id": account_id, "category_id": category_id, "type": type,
        "uncategorized": uncategorized, "q": q, "date_from": date_from, "date_to": date_to,
    }
    txns = await list_transactions(db, user.id, filters)
    accounts = await get_account_balances(db, user.id)
    categories = await _flat_categories(db, user.id)
    return templates.TemplateResponse(
        request, "transactions.html",
        {"txns": txns, "accounts": accounts, "categories": categories, "today": date.today().isoformat(), "filters": filters},
    )


@router.post("/txn")
async def create_txn(
    request: Request,
    account_id: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    merchant_clean: str | None = Form(None),
    category_id: str | None = Form(None),
    txn_date: date = Form(...),
    notes: str | None = Form(None),
    tags: str | None = Form(None),
    transfer_account_id: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    category_id = category_id or None
    transfer_account_id = transfer_account_id if type == "transfer" else None

    txn_id, is_dup = await create_transaction(
        db, user.id,
        account_id=account_id, type=type, amount=amount, txn_date=txn_date,
        merchant_raw=merchant_clean, merchant_clean=merchant_clean,
        category_id=category_id, notes=notes, transfer_account_id=transfer_account_id,
    )
    await set_transaction_tags(db, user.id, txn_id, _parse_tags(tags))

    row = await get_transaction(db, user.id, txn_id)
    return templates.TemplateResponse(
        request, "partials/txn_row.html", {"t": row, "is_duplicate_warning": is_dup}
    )


@router.get("/txn/{txn_id}")
async def get_txn_row(
    request: Request,
    txn_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    row = await get_transaction(db, user.id, txn_id)
    return templates.TemplateResponse(request, "partials/txn_row.html", {"t": row})


@router.get("/txn/{txn_id}/edit")
async def edit_txn_row(
    request: Request,
    txn_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    row = await get_transaction(db, user.id, txn_id)
    return templates.TemplateResponse(request, "partials/txn_edit_row.html", {"t": row})


@router.patch("/txn/{txn_id}")
async def patch_txn(
    request: Request,
    txn_id: str,
    txn_date: date | None = Form(None),
    merchant_clean: str | None = Form(None),
    amount: float | None = Form(None),
    notes: str | None = Form(None),
    category_id: str | None = Form(None),
    tags: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    # Detect a genuine recategorization to a real category, to offer correction-learning (§4.1 step 4).
    prev_category_id = None
    if category_id is not None and category_id != "":
        prev_category_id = (
            await db.execute(
                text("SELECT category_id FROM transactions WHERE id=:tid AND user_id=:uid"),
                {"tid": txn_id, "uid": user.id},
            )
        ).scalar()

    fields = {"txn_date": txn_date, "merchant_clean": merchant_clean, "amount": amount, "notes": notes}
    if category_id == "":
        # update_transaction's None means "not provided" (skip); an explicit clear needs its own statement.
        await db.execute(
            text("UPDATE transactions SET category_id = NULL, updated_at = now() WHERE id=:tid AND user_id=:uid"),
            {"tid": txn_id, "uid": user.id},
        )
    elif category_id is not None:
        fields["category_id"] = category_id
    await update_transaction(db, user.id, txn_id, fields)
    if tags is not None:
        await set_transaction_tags(db, user.id, txn_id, _parse_tags(tags))

    row = await get_transaction(db, user.id, txn_id)

    changed_category = (
        category_id is not None
        and category_id != ""
        and str(prev_category_id) != str(category_id)
        and (row["merchant_raw"] or row["merchant_clean"])
    )
    ctx = {"t": row}
    if changed_category:
        ctx["learn_offer"] = {
            "txn_id": txn_id,
            "merchant": row["merchant_clean"] or row["merchant_raw"],
            "category_id": category_id,
            "category_name": row["category_name"],
        }
    return templates.TemplateResponse(request, "partials/txn_row.html", ctx)


@router.delete("/txn/{txn_id}")
async def delete_txn(
    request: Request,
    txn_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await soft_delete_transaction(db, user.id, txn_id)
    placeholder = f'<tr id="txn-row-{txn_id}" style="display:none"></tr>'
    toast = templates.get_template("partials/toast.html").render(
        message="Transaction deleted.", undo_url=f"/txn/{txn_id}/undo", undo_target=f"#txn-row-{txn_id}"
    )
    return HTMLResponse(content=placeholder + toast)


@router.post("/txn/{txn_id}/undo")
async def undo_delete_txn(
    request: Request,
    txn_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await restore_transaction(db, user.id, txn_id)
    row = await get_transaction(db, user.id, txn_id)
    return templates.TemplateResponse(request, "partials/txn_row.html", {"t": row})


@router.post("/txn/bulk")
async def bulk_action(
    request: Request,
    action: str = Form(...),
    txn_ids: list[str] = Form([]),
    bulk_category_id: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    if action == "delete":
        await bulk_delete(db, user.id, txn_ids)
    elif action == "category":
        await bulk_set_category(db, user.id, txn_ids, bulk_category_id or None)

    txns = await list_transactions(db, user.id, {})
    accounts = await get_account_balances(db, user.id)
    categories = await _flat_categories(db, user.id)
    return templates.TemplateResponse(
        request, "partials/txn_table.html", {"txns": txns, "accounts": accounts, "categories": categories}
    )


@router.post("/txn/quickadd/preview")
async def quickadd_preview(
    request: Request,
    raw: str = Form(""),
    category_override_id: str = Form(""),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    if not raw.strip():
        return HTMLResponse("")
    preview = await build_quickadd_preview(db, user.id, raw, category_override_id=category_override_id or None)
    return templates.TemplateResponse(request, "partials/quick_add_result.html", {"p": preview, "mode": "preview"})


@router.post("/txn/quickadd")
async def quickadd_commit(
    request: Request,
    raw: str = Form(...),
    category_override_id: str = Form(""),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    preview = await build_quickadd_preview(db, user.id, raw, category_override_id=category_override_id or None)
    parsed = preview["parsed"]

    if parsed.amount is None or preview["account"] is None:
        return templates.TemplateResponse(
            request, "partials/quick_add_result.html", {"p": preview, "mode": "error"}
        )

    txn_type = "income" if parsed.is_income else "expense"
    txn_id, is_dup = await create_transaction(
        db, user.id,
        account_id=str(preview["account"]["id"]), type=txn_type, amount=parsed.amount, txn_date=parsed.txn_date,
        merchant_raw=parsed.merchant_token, merchant_clean=preview["merchant_clean"],
        category_id=preview["category_id"], notes=parsed.note, source="quickadd",
    )
    if parsed.tags:
        await set_transaction_tags(db, user.id, txn_id, parsed.tags)

    success_html = templates.get_template("partials/quick_add_success.html").render(
        p=preview, txn_id=txn_id, is_duplicate_warning=is_dup
    )
    # #txn-tbody only exists on the /txn page; harmless no-op elsewhere (htmx skips missing OOB targets).
    row = await get_transaction(db, user.id, txn_id)
    row_html = templates.get_template("partials/txn_row.html").render(t=row, is_duplicate_warning=is_dup)
    oob_row = f'<div hx-swap-oob="afterbegin:#txn-tbody">{row_html}</div>'
    return HTMLResponse(content=success_html + oob_row)
