---
source_file: "lens/app/auth/deps.py"
type: "rationale"
community: "routes.py"
location: "L34"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/routespy
---

# Verifies the Supabase JWT and extracts user_id (= auth.uid()), per §2.3 step 4.

## Connections
- [[get_current_user()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/routespy