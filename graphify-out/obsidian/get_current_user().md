---
source_file: "lens/app/auth/deps.py"
type: "code"
community: "routes.py"
location: "L33"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/routespy
---

# get_current_user()

## Connections
- [[CurrentUser]] - `references` [EXTRACTED]
- [[HTTPException]] - `calls` [INFERRED]
- [[Request]] - `references` [EXTRACTED]
- [[Response]] - `references` [EXTRACTED]
- [[Verifies the Supabase JWT and extracts user_id (= auth.uid()), per §2.3 step 4.]] - `rationale_for` [EXTRACTED]
- [[_refresh_access_token()]] - `calls` [EXTRACTED]
- [[deps.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/routespy