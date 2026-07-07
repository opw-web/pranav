---
type: community
members: 20
---

# transactions.py

**Members:** 20 nodes

## Members
- [[AsyncSession_6]] - code
- [[Deterministic analytics — SQL-first (§2.6, §4.4). Python only orchestrates and t]] - rationale - lens/app/services/analytics.py
- [[First day of d's month and first day of next month (half-open start, end)).]] - rationale - lens/app/services/analytics.py
- [[Median monthly expense per category over the last 3 full months (PERCENTILE_CONT]] - rationale - lens/app/services/analytics.py
- [[Period-over-period attribution at category + merchant level. Returns ranked driv]] - rationale - lens/app/services/analytics.py
- [[SUM(amount) WHERE tag GROUP BY category. Transfers excluded (they aren't spend).]] - rationale - lens/app/services/analytics.py
- [[start, end) covering the n full calendar months before d's month.]] - rationale - lens/app/services/analytics.py
- [[_deltas()]] - code - lens/app/services/analytics.py
- [[_essential_category_ids()]] - code - lens/app/services/analytics.py
- [[analytics.py]] - code - lens/app/services/analytics.py
- [[category_normals()]] - code - lens/app/services/analytics.py
- [[date_1]] - code
- [[last_n_full_months()]] - code - lens/app/services/analytics.py
- [[month_bounds()]] - code - lens/app/services/analytics.py
- [[prev_month_bounds()]] - code - lens/app/services/analytics.py
- [[safe_to_spend()]] - code - lens/app/services/analytics.py
- [[spendable_balance − upcoming_committed − essential_remaining, with the breakdown]] - rationale - lens/app/services/analytics.py
- [[spending_detective()]] - code - lens/app/services/analytics.py
- [[trip_rollup()]] - code - lens/app/services/analytics.py
- [[what_changed()]] - code - lens/app/services/analytics.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/transactionspy
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_UX Playbook Spec]]

## Top bridge nodes
- [[safe_to_spend()]] - degree 8, connects to 1 community