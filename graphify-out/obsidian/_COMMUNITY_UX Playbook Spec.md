---
type: community
members: 17
---

# UX Playbook Spec

**Members:** 17 nodes

## Members
- [[AsyncSession]] - code
- [[AsyncSession_5]] - code
- [[AsyncSession_11]] - code
- [[Creates a visible adjustment transaction closing the gap between the computed]] - rationale - lens/app/services/reconcile.py
- [[Request_3]] - code
- [[Shared account-balance query, used by the accounts router, reconcile, and (later]] - rationale - lens/app/services/balances.py
- [[accounts.py]] - code - lens/app/routers/accounts.py
- [[archive_account()]] - code - lens/app/routers/accounts.py
- [[balances.py]] - code - lens/app/services/balances.py
- [[create_account()]] - code - lens/app/routers/accounts.py
- [[get_account_balances()]] - code - lens/app/services/balances.py
- [[get_single_account_balance()]] - code - lens/app/services/balances.py
- [[list_accounts()]] - code - lens/app/routers/accounts.py
- [[reconcile()]] - code - lens/app/routers/accounts.py
- [[reconcile.py]] - code - lens/app/services/reconcile.py
- [[reconcile_account()]] - code - lens/app/services/reconcile.py
- [[rename_account()]] - code - lens/app/routers/accounts.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/UX_Playbook_Spec
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_CurrentUser]]
- 1 edge to [[_COMMUNITY_session.py_1]]

## Top bridge nodes
- [[get_account_balances()]] - degree 9, connects to 2 communities
- [[reconcile()]] - degree 6, connects to 1 community
- [[list_accounts()]] - degree 5, connects to 1 community
- [[create_account()]] - degree 5, connects to 1 community
- [[rename_account()]] - degree 5, connects to 1 community