import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.balances import get_single_account_balance


async def reconcile_account(session: AsyncSession, user_id: str, account_id: str, actual_balance: float) -> dict:
    """Creates a visible adjustment transaction closing the gap between the computed
    and the user-reported actual balance. Never silently edits opening_balance (§7 Check 12)."""
    current = await get_single_account_balance(session, user_id, account_id)
    if current is None:
        return {"created": False, "diff": 0}

    diff = round(float(actual_balance) - float(current["balance"]), 2)
    if diff == 0:
        return {"created": False, "diff": 0}

    txn_type = "income" if diff > 0 else "expense"
    amount = abs(diff)
    txn_id = str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO transactions (id, user_id, account_id, type, amount, currency, txn_date, notes, source) "
            "VALUES (:id, :uid, :aid, :type, :amount, :currency, CURRENT_DATE, 'Balance reconciliation adjustment', 'manual')"
        ),
        {
            "id": txn_id,
            "uid": user_id,
            "aid": account_id,
            "type": txn_type,
            "amount": amount,
            "currency": current["currency"],
        },
    )
    return {"created": True, "diff": diff, "txn_id": txn_id}
