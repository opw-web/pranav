---
source_file: "lens/app/services/recurring_detector.py"
type: "rationale"
community: "detect_series_for_merchant"
location: "L41"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/detect_series_for_merchant
---

# All amounts within ±tolerance of the median (subscriptions wobble a little).

## Connections
- [[_amount_is_stable()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/detect_series_for_merchant