import base64
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services import importer
from app.services.import_commit import (
    build_preview,
    commit_chunk,
    recall_column_mapping,
    save_column_mapping,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

ROLES = ["date", "amount", "debit", "credit", "desc"]


def _b64(text_str: str) -> str:
    return base64.b64encode(text_str.encode()).decode()


def _unb64(b: str) -> str:
    return base64.b64decode(b.encode()).decode()


async def _accounts(db, user_id):
    return (
        await db.execute(
            text("SELECT id, name FROM accounts WHERE user_id=:uid AND is_archived=FALSE ORDER BY name"),
            {"uid": user_id},
        )
    ).mappings().all()


@router.get("/import")
async def import_page(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    accounts = await _accounts(db, user.id)
    return templates.TemplateResponse(request, "import_wizard.html", {"accounts": accounts})


@router.post("/import/upload")
async def upload(
    request: Request,
    file: UploadFile,
    account_id: str = Form(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    raw = await file.read()
    info = importer.analyze(raw)
    text_content = importer.decode_bytes(raw)

    remembered = await recall_column_mapping(db, user.id, info["signature"])
    if remembered:
        info["mapping"] = remembered["mapping"]
        info["date_format"] = remembered["date_format"]
        info["amount_convention"] = remembered["amount_convention"]

    return templates.TemplateResponse(
        request,
        "partials/import_mapping.html",
        {
            "info": info,
            "roles": ROLES,
            "account_id": account_id,
            "filename": file.filename,
            "file_b64": _b64(text_content),
            "recognized": bool(remembered),
        },
    )


def _parse_form_mapping(form) -> dict:
    mapping = {}
    for role in ROLES:
        col = form.get(f"map_{role}")
        if col:
            mapping[role] = col
    return mapping


@router.post("/import/preview")
async def preview(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    form = await request.form()
    account_id = form["account_id"]
    file_b64 = form["file_b64"]
    delimiter = form["delimiter"]
    header_idx = int(form["header_idx"])
    date_format = form.get("date_format") or None
    mapping = _parse_form_mapping(form)
    amount_convention = importer.detect_amount_convention(mapping)

    text_content = _unb64(file_b64)
    header, data = importer.parse_rows(text_content, delimiter, header_idx)
    txns = importer.extract_transactions(header, data, mapping, date_format, amount_convention)
    prev = await build_preview(db, user.id, account_id, txns)

    return templates.TemplateResponse(
        request,
        "partials/import_preview.html",
        {
            "preview": prev,
            "account_id": account_id,
            "file_b64": file_b64,
            "delimiter": delimiter,
            "header_idx": header_idx,
            "date_format": date_format or "",
            "mapping_json": json.dumps(mapping),
            "signature": importer.bank_signature(header),
            "amount_convention": amount_convention,
        },
    )


@router.post("/import/commit")
async def commit(
    request: Request,
    page: int = 0,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    form = await request.form()
    account_id = form["account_id"]
    file_b64 = form["file_b64"]
    delimiter = form["delimiter"]
    header_idx = int(form["header_idx"])
    date_format = form.get("date_format") or None
    mapping = json.loads(form["mapping_json"])
    amount_convention = form["amount_convention"]
    signature = form["signature"]
    batch_id = form.get("batch_id") or None

    text_content = _unb64(file_b64)
    header, data = importer.parse_rows(text_content, delimiter, header_idx)
    txns = importer.extract_transactions(header, data, mapping, date_format, amount_convention)

    if batch_id is None:
        batch_id = str(uuid.uuid4())
        await db.execute(
            text(
                "INSERT INTO import_batches (id, user_id, account_id, filename, row_count, status) "
                "VALUES (:id,:uid,:aid,:fn,:rc,'running')"
            ),
            {"id": batch_id, "uid": user.id, "aid": account_id, "fn": form.get("filename"), "rc": len(txns)},
        )
        await save_column_mapping(db, user.id, signature, mapping, date_format, amount_convention)

    start, end, has_more = importer.chunk_bounds(len(txns), page)
    result = await commit_chunk(db, user.id, account_id, batch_id, txns, start, end)

    # accumulate running totals across chunks via query params echoed in the fragment
    running_imported = int(form.get("running_imported", 0)) + result["imported"]
    running_skipped = int(form.get("running_skipped", 0)) + result["skipped"]
    running_review = int(form.get("running_review", 0)) + result["needs_review"]

    if not has_more:
        await db.execute(
            text("UPDATE import_batches SET status='done' WHERE id=:bid AND user_id=:uid"),
            {"bid": batch_id, "uid": user.id},
        )

    return templates.TemplateResponse(
        request,
        "partials/import_progress.html",
        {
            "done": not has_more,
            "next_page": page + 1,
            "processed": end,
            "total": len(txns),
            "imported": running_imported,
            "skipped": running_skipped,
            "needs_review": running_review,
            "batch_id": batch_id,
            "account_id": account_id,
            "file_b64": file_b64,
            "delimiter": delimiter,
            "header_idx": header_idx,
            "date_format": date_format or "",
            "mapping_json": json.dumps(mapping),
            "amount_convention": amount_convention,
            "signature": signature,
        },
    )
