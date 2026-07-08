---
type: community
members: 27
---

# confirm

**Members:** 27 nodes

## Members
- [[Activate a detected series; recompute next_due_date from last_seen + cadence (§4]] - rationale - lens/app/services/recurring.py
- [[Active series due between today and today+within_days — feeds the dashboard and]] - rationale - lens/app/services/recurring.py
- [[AsyncSession_2]] - code
- [[AsyncSession_6]] - code
- [[AsyncSession_19]] - code
- [[DB-facing recurring-series operations scan history - upsert detected series, c]] - rationale - lens/app/services/recurring.py
- [[Format a numeric amount with tabular-friendly grouping and a currency symbol.]] - rationale - lens/app/templating.py
- [[Group the user's expense history by merchant_clean, detect series, and upsert]] - rationale - lens/app/services/recurring.py
- [[Request_5]] - code
- [[Request_9]] - code
- [[Return an inline svguse referencing the vendored Phosphor sprite.      Usage]] - rationale - lens/app/templating.py
- [[Return the display symbol for a currency code, falling back to the code itself.]] - rationale - lens/app/templating.py
- [[Shared Jinja2 templates instance for every router.  Single source of truth so al]] - rationale - lens/app/templating.py
- [[confirm()]] - code - lens/app/routers/recurring.py
- [[confirm_series()]] - code - lens/app/services/recurring.py
- [[currency_symbol()]] - code - lens/app/templating.py
- [[dashboard()]] - code - lens/app/routers/dashboard.py
- [[dashboard.py]] - code - lens/app/routers/dashboard.py
- [[icon()]] - code - lens/app/templating.py
- [[list_series()]] - code - lens/app/services/recurring.py
- [[money()]] - code - lens/app/templating.py
- [[recurring.py]] - code - lens/app/routers/recurring.py
- [[recurring.py_1]] - code - lens/app/services/recurring.py
- [[recurring_page()]] - code - lens/app/routers/recurring.py
- [[scan_and_upsert()]] - code - lens/app/services/recurring.py
- [[templating.py]] - code - lens/app/templating.py
- [[upcoming()]] - code - lens/app/services/recurring.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/confirm
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_CurrentUser]]
- 3 edges to [[_COMMUNITY_transactions.py]]
- 1 edge to [[_COMMUNITY_UX Playbook Spec]]
- 1 edge to [[_COMMUNITY_Backend Service Requirements]]
- 1 edge to [[_COMMUNITY_main.py]]
- 1 edge to [[_COMMUNITY_Database Schema & Architecture]]
- 1 edge to [[_COMMUNITY_detect_series_for_merchant]]

## Top bridge nodes
- [[templating.py]] - degree 11, connects to 5 communities
- [[dashboard()]] - degree 8, connects to 2 communities
- [[recurring_page()]] - degree 7, connects to 1 community
- [[confirm()]] - degree 7, connects to 1 community
- [[scan_and_upsert()]] - degree 5, connects to 1 community