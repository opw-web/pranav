"""Shared account-balance query, used by the accounts router, reconcile, and (later) safe-to-spend.

Formula (§4.4): balance = opening_balance + income + refunds − expense ± transfers.
A transfer is one row: it debits `account_id` (the source) and credits
`transfer_account_id` (the destination) — never counted as expense/income.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

BALANCES_SQL = """
WITH outgoing AS (
    SELECT account_id,
        SUM(CASE
            WHEN type = 'income'   THEN amount
            WHEN type = 'refund'   THEN amount
            WHEN type = 'expense'  THEN -amount
            WHEN type = 'transfer' THEN -amount
            ELSE 0
        END) AS net
    FROM transactions
    WHERE user_id = :uid AND is_deleted = FALSE
    GROUP BY account_id
),
incoming_transfers AS (
    SELECT transfer_account_id AS account_id, SUM(amount) AS net
    FROM transactions
    WHERE user_id = :uid AND is_deleted = FALSE AND type = 'transfer' AND transfer_account_id IS NOT NULL
    GROUP BY transfer_account_id
)
SELECT
    a.id, a.name, a.type, a.currency, a.is_spendable, a.is_archived, a.opening_balance,
    a.opening_balance + COALESCE(o.net, 0) + COALESCE(i.net, 0) AS balance
FROM accounts a
LEFT JOIN outgoing o ON o.account_id = a.id
LEFT JOIN incoming_transfers i ON i.account_id = a.id
WHERE a.user_id = :uid
ORDER BY a.is_archived, a.created_at
"""


async def get_account_balances(session: AsyncSession, user_id: str):
    result = await session.execute(text(BALANCES_SQL), {"uid": user_id})
    return result.mappings().all()


async def get_single_account_balance(session: AsyncSession, user_id: str, account_id: str):
    for row in await get_account_balances(session, user_id):
        if str(row["id"]) == str(account_id):
            return row
    return None
