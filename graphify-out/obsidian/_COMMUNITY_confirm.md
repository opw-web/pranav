---
type: community
members: 15
---

# confirm

**Members:** 15 nodes

## Members
- [[Activate a detected series; recompute next_due_date from last_seen + cadence (§4]] - rationale - lens/app/services/recurring.py
- [[Active series due between today and today+within_days — feeds the dashboard and]] - rationale - lens/app/services/recurring.py
- [[AsyncSession_6]] - code
- [[AsyncSession_19]] - code
- [[DB-facing recurring-series operations scan history - upsert detected series, c]] - rationale - lens/app/services/recurring.py
- [[Group the user's expense history by merchant_clean, detect series, and upsert]] - rationale - lens/app/services/recurring.py
- [[Request_9]] - code
- [[confirm()]] - code - lens/app/routers/recurring.py
- [[confirm_series()]] - code - lens/app/services/recurring.py
- [[list_series()]] - code - lens/app/services/recurring.py
- [[recurring.py]] - code - lens/app/routers/recurring.py
- [[recurring.py_1]] - code - lens/app/services/recurring.py
- [[recurring_page()]] - code - lens/app/routers/recurring.py
- [[scan_and_upsert()]] - code - lens/app/services/recurring.py
- [[upcoming()]] - code - lens/app/services/recurring.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/confirm
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_CurrentUser]]
- 1 edge to [[_COMMUNITY_transactions.py]]
- 1 edge to [[_COMMUNITY_detect_series_for_merchant]]

## Top bridge nodes
- [[recurring_page()]] - degree 7, connects to 1 community
- [[confirm()]] - degree 7, connects to 1 community
- [[upcoming()]] - degree 6, connects to 1 community
- [[scan_and_upsert()]] - degree 5, connects to 1 community