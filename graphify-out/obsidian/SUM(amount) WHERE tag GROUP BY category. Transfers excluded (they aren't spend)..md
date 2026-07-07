---
source_file: "lens/app/services/analytics.py"
type: "rationale"
community: "transactions.py"
location: "L309"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/transactionspy
---

# SUM(amount) WHERE tag GROUP BY category. Transfers excluded (they aren't spend).

## Connections
- [[trip_rollup()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/transactionspy