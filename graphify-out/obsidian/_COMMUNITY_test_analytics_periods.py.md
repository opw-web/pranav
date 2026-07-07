---
type: community
members: 9
---

# test_analytics_periods.py

**Members:** 9 nodes

## Members
- [[Pure period-boundary math for analytics (§4.4). A wrong boundary silently corrup]] - rationale - lens/tests/test_analytics_periods.py
- [[test_analytics_periods.py]] - code - lens/tests/test_analytics_periods.py
- [[test_cur_and_prev_are_contiguous_and_non_overlapping()]] - code - lens/tests/test_analytics_periods.py
- [[test_last_3_full_months_crosses_year()]] - code - lens/tests/test_analytics_periods.py
- [[test_last_3_full_months_excludes_current()]] - code - lens/tests/test_analytics_periods.py
- [[test_month_bounds_december_rolls_year()]] - code - lens/tests/test_analytics_periods.py
- [[test_month_bounds_mid_year()]] - code - lens/tests/test_analytics_periods.py
- [[test_prev_month_bounds_january_rolls_back()]] - code - lens/tests/test_analytics_periods.py
- [[test_prev_month_bounds_mid_year()]] - code - lens/tests/test_analytics_periods.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_analytics_periodspy
SORT file.name ASC
```
