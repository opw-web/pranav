---
type: community
members: 31
---

# routes.py

**Members:** 31 nodes

## Members
- [[AsyncSession_9]] - code
- [[DB session for the current request app-level scope (user.id) is layered     on]] - rationale - lens/app/auth/deps.py
- [[First-login seed (§4.6) starter category tree + a default Cash account.     Ide]] - rationale - lens/app/services/onboarding.py
- [[HTTPException]] - code
- [[Plain session, no RLS context. Only for adminglobal reads (e.g. merchant_seed).]] - rationale - lens/app/database.py
- [[Request]] - code
- [[Request_1]] - code
- [[Request_2]] - code
- [[Response]] - code
- [[Session scoped to a specific user for the duration of one transaction.      Our]] - rationale - lens/app/database.py
- [[Settings]] - code - lens/app/config.py
- [[Verifies the Supabase JWT and extracts user_id (= auth.uid()), per §2.3 step 4.]] - rationale - lens/app/auth/deps.py
- [[_refresh_access_token()]] - code - lens/app/auth/deps.py
- [[auth_callback()]] - code - lens/app/auth/routes.py
- [[auth_google_start()]] - code - lens/app/auth/routes.py
- [[auth_redirect_handler()]] - code - lens/app/main.py
- [[config.py]] - code - lens/app/config.py
- [[database.py]] - code - lens/app/database.py
- [[deps.py]] - code - lens/app/auth/deps.py
- [[ensure_onboarded()]] - code - lens/app/services/onboarding.py
- [[get_current_user()]] - code - lens/app/auth/deps.py
- [[get_db()]] - code - lens/app/database.py
- [[get_scoped_db()]] - code - lens/app/database.py
- [[get_scoped_session()]] - code - lens/app/auth/deps.py
- [[healthz()]] - code - lens/app/main.py
- [[login_page()]] - code - lens/app/auth/routes.py
- [[logout()]] - code - lens/app/auth/routes.py
- [[main.py]] - code - lens/app/main.py
- [[onboarding.py]] - code - lens/app/services/onboarding.py
- [[root()]] - code - lens/app/main.py
- [[routes.py]] - code - lens/app/auth/routes.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/routespy
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_CurrentUser]]
- 1 edge to [[_COMMUNITY_session.py]]

## Top bridge nodes
- [[get_current_user()]] - degree 7, connects to 1 community
- [[deps.py]] - degree 6, connects to 1 community
- [[config.py]] - degree 5, connects to 1 community
- [[get_scoped_session()]] - degree 4, connects to 1 community
- [[root()]] - degree 3, connects to 1 community