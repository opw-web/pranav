import csv
import io
import json
from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.savings import get_user_settings, save_user_settings
from app.templating import templates

router = APIRouter()


def _parse_optional_amount(raw: str | None) -> float | None:
    """Parse a form value into a non-negative float, or None for "no value".

    Never raises: unparseable input (e.g. "abc") or a negative number is treated
    as "no change" rather than 500ing the request.
    """
    if raw is None or str(raw).strip() == "":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    return value

# Full row with human-readable names (not just ids) so the backup restores standalone (Check 15).
_EXPORT_SQL = """
SELECT t.txn_date, t.txn_time, t.type, t.amount, t.currency,
       t.merchant_raw, t.merchant_clean,
       a.name AS account, ta.name AS transfer_account,
       COALESCE(pc.name || ' > ' || c.name, c.name) AS category,
       t.notes, t.is_reimbursable, t.is_pending, t.source,
       COALESCE(string_agg(tg.name, '|' ORDER BY tg.name), '') AS tags
FROM transactions t
JOIN accounts a ON a.id = t.account_id
LEFT JOIN accounts ta ON ta.id = t.transfer_account_id
LEFT JOIN categories c ON c.id = t.category_id
LEFT JOIN categories pc ON pc.id = c.parent_id
LEFT JOIN transaction_tags tt ON tt.transaction_id = t.id
LEFT JOIN tags tg ON tg.id = tt.tag_id
WHERE t.user_id = :uid AND t.is_deleted = FALSE
GROUP BY t.id, a.name, ta.name, c.name, pc.name
ORDER BY t.txn_date, t.created_at
"""

_COLUMNS = [
    "txn_date", "txn_time", "type", "amount", "currency", "merchant_raw", "merchant_clean",
    "account", "transfer_account", "category", "notes", "is_reimbursable", "is_pending", "source", "tags",
]


@router.get("/settings")
async def settings_page(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    prefs = await get_user_settings(db, user.id)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "user": user,
            "current_period": date.today().strftime("%Y-%m"),
            "monthly_income": prefs["monthly_income"],
            "savings_goal": prefs["savings_goal"],
            "saved": request.query_params.get("saved") == "1",
        },
    )


@router.post("/settings/income")
async def save_income_settings(
    monthly_income: str = Form(""),
    savings_goal: str = Form(""),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await save_user_settings(
        db,
        user.id,
        _parse_optional_amount(monthly_income),
        _parse_optional_amount(savings_goal),
    )
    return RedirectResponse("/settings?saved=1", status_code=303)


async def _fetch_rows(db: AsyncSession, user_id: str):
    return (await db.execute(text(_EXPORT_SQL), {"uid": user_id})).mappings().all()


@router.get("/settings/export")
async def export_csv(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    rows = await _fetch_rows(db, user.id)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_COLUMNS)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: ("" if r[k] is None else r[k]) for k in _COLUMNS})
    buf.seek(0)
    fname = f"lens-export-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/settings/export.json")
async def export_json(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    rows = await _fetch_rows(db, user.id)
    payload = json.dumps(
        [{k: (str(r[k]) if r[k] is not None else None) for k in _COLUMNS} for r in rows],
        indent=2,
    )
    fname = f"lens-export-{date.today().isoformat()}.json"
    return StreamingResponse(
        iter([payload]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
