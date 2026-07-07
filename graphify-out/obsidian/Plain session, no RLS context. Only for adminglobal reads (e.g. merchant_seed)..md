---
source_file: "lens/app/database.py"
type: "rationale"
community: "routes.py"
location: "L26"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/routespy
---

# Plain session, no RLS context. Only for admin/global reads (e.g. merchant_seed).

## Connections
- [[get_db()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/routespy