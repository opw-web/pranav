---
source_file: "lens/app/services/recurring_detector.py"
type: "code"
community: "detect_series_for_merchant"
location: "L50"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/detect_series_for_merchant
---

# detect_series_for_merchant()

## Connections
- [[DetectedSeries]] - `references` [EXTRACTED]
- [[_amount_is_stable()]] - `calls` [EXTRACTED]
- [[_classify_cadence()]] - `calls` [EXTRACTED]
- [[date_4]] - `references` [EXTRACTED]
- [[detect_all()]] - `calls` [EXTRACTED]
- [[points = (date, amount), ... for one merchant. Returns a series if a regular]] - `rationale_for` [EXTRACTED]
- [[recurring_detector.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/detect_series_for_merchant