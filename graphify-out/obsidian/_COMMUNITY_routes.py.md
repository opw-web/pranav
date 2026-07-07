---
type: community
members: 45
---

# routes.py

**Members:** 45 nodes

## Members
- [[AsyncSession_15]] - code
- [[DB session for the current request app-level scope (user.id) is layered     on]] - rationale - lens/app/auth/deps.py
- [[Find active series due within 3 days, and flag renewals that came in higher than]] - rationale - lens/app/routers/cron.py
- [[First-login seed (§4.6) starter category tree + a default Cash account.     Ide]] - rationale - lens/app/services/onboarding.py
- [[HTTPException]] - code
- [[Plain session, no RLS context. Only for adminglobal reads (e.g. merchant_seed).]] - rationale - lens/app/database.py
- [[Request]] - code
- [[Request_1]] - code
- [[Request_2]] - code
- [[Response]] - code
- [[Scheduled jobs invoked by Vercel Cron (§4.3). Not user-facing protected by a sh]] - rationale - lens/app/routers/cron.py
- [[Session scoped to a specific user for the duration of one transaction.      Our]] - rationale - lens/app/database.py
- [[Settings]] - code - lens/app/config.py
- [[Vercel serverless entrypoint. Vercel's @vercelpython runtime serves the ASGI `a]] - rationale - lens/api/index.py
- [[Verifies the Supabase JWT and extracts user_id (= auth.uid()), per §2.3 step 4.]] - rationale - lens/app/auth/deps.py
- [[Verify a Supabase-issued JWT locally against the project's JWKS (ES256).     Rai]] - rationale - lens/app/auth/session.py
- [[_authorize()]] - code - lens/app/routers/cron.py
- [[_fetch_jwks()]] - code - lens/app/auth/session.py
- [[_refresh_access_token()]] - code - lens/app/auth/deps.py
- [[auth_callback()]] - code - lens/app/auth/routes.py
- [[auth_google_start()]] - code - lens/app/auth/routes.py
- [[auth_redirect_handler()]] - code - lens/app/main.py
- [[clear_session_cookies()]] - code - lens/app/auth/session.py
- [[config.py]] - code - lens/app/config.py
- [[cron.py]] - code - lens/app/routers/cron.py
- [[database.py]] - code - lens/app/database.py
- [[deps.py]] - code - lens/app/auth/deps.py
- [[ensure_onboarded()]] - code - lens/app/services/onboarding.py
- [[generate_pkce_pair()]] - code - lens/app/auth/session.py
- [[get_current_user()]] - code - lens/app/auth/deps.py
- [[get_db()]] - code - lens/app/database.py
- [[get_scoped_db()]] - code - lens/app/database.py
- [[get_scoped_session()]] - code - lens/app/auth/deps.py
- [[healthz()]] - code - lens/app/main.py
- [[index.py]] - code - lens/api/index.py
- [[is_secure_request()]] - code - lens/app/auth/session.py
- [[login_page()]] - code - lens/app/auth/routes.py
- [[logout()]] - code - lens/app/auth/routes.py
- [[main.py]] - code - lens/app/main.py
- [[onboarding.py]] - code - lens/app/services/onboarding.py
- [[recurring_reminders()]] - code - lens/app/routers/cron.py
- [[routes.py]] - code - lens/app/auth/routes.py
- [[session.py]] - code - lens/app/auth/session.py
- [[set_session_cookies()]] - code - lens/app/auth/session.py
- [[verify_access_token()]] - code - lens/app/auth/session.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/routespy
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_CurrentUser]]

## Top bridge nodes
- [[get_current_user()]] - degree 7, connects to 1 community
- [[deps.py]] - degree 6, connects to 1 community
- [[get_scoped_session()]] - degree 4, connects to 1 community