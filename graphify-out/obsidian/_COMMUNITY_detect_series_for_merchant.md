---
type: community
members: 11
---

# detect_series_for_merchant

**Members:** 11 nodes

## Members
- [[All amounts within ±tolerance of the median (subscriptions wobble a little).]] - rationale - lens/app/services/recurring_detector.py
- [[DetectedSeries]] - code - lens/app/services/recurring_detector.py
- [[Recurring-series detection (§4.3). The cadenceamount-stability analysis is pure]] - rationale - lens/app/services/recurring_detector.py
- [[_amount_is_stable()]] - code - lens/app/services/recurring_detector.py
- [[_classify_cadence()]] - code - lens/app/services/recurring_detector.py
- [[date_5]] - code
- [[detect_all()]] - code - lens/app/services/recurring_detector.py
- [[detect_series_for_merchant()]] - code - lens/app/services/recurring_detector.py
- [[grouped = {merchant_clean (date, amount), ...}. Returns all detected series.]] - rationale - lens/app/services/recurring_detector.py
- [[points = (date, amount), ... for one merchant. Returns a series if a regular]] - rationale - lens/app/services/recurring_detector.py
- [[recurring_detector.py]] - code - lens/app/services/recurring_detector.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/detect_series_for_merchant
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_confirm]]

## Top bridge nodes
- [[detect_all()]] - degree 6, connects to 1 community