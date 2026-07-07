---
type: community
members: 11
---

# test_recurring.py

**Members:** 11 nodes

## Members
- [[Pure-Python recurring-detection tests — no DB (§4.3, §7 recurring behavior).]] - rationale - lens/tests/test_recurring.py
- [[_monthly()]] - code - lens/tests/test_recurring.py
- [[date_6]] - code
- [[test_detect_all_skips_empty_merchant()]] - code - lens/tests/test_recurring.py
- [[test_detects_monthly_subscription()]] - code - lens/tests/test_recurring.py
- [[test_detects_weekly()]] - code - lens/tests/test_recurring.py
- [[test_recurring.py]] - code - lens/tests/test_recurring.py
- [[test_rejects_irregular_interval()]] - code - lens/tests/test_recurring.py
- [[test_rejects_wild_amount_variation()]] - code - lens/tests/test_recurring.py
- [[test_requires_min_occurrences()]] - code - lens/tests/test_recurring.py
- [[test_tolerates_small_amount_wobble()]] - code - lens/tests/test_recurring.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_recurringpy
SORT file.name ASC
```
