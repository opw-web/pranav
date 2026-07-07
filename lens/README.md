# LENS — the expense app that shows you *why*

Deterministic, cloud, multi-user expense manager. FastAPI + Jinja + HTMX + Alpine, Supabase (Postgres + Google auth), no AI. See `../LENS_V1_BUILD_PLAN.md` for the full spec.

## Local development

```bash
cd lens
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in the values below
./scripts/build_css.sh        # build Tailwind output (needs scripts/tailwindcss binary)
uvicorn app.main:app --reload --port 8001
```

Download the Tailwind standalone binary once:
`curl -sL https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64 -o scripts/tailwindcss && chmod +x scripts/tailwindcss`

## Environment variables

| Var | Where to get it |
|-----|-----------------|
| `SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_ANON_KEY` | same |
| `SUPABASE_SERVICE_ROLE_KEY` | same (server-only, never shipped to browser) |
| `DATABASE_URL` | Supabase → Database → Connection string (use the **transaction pooler**, port 6543, driver `postgresql+asyncpg://`) |
| `SESSION_SECRET` | any random string |
| `CRON_SECRET` | any random string; Vercel Cron sends it as `Authorization: Bearer` |
| `GOOGLE_REDIRECT_URL` | `<your-domain>/auth/callback` |

## Database setup

Run migrations against your Supabase project (SQL editor or psql):
`migrations/001_init.sql`, `002_rls.sql`, `003_indexes.sql`, then
`python scripts/load_merchant_seed.py` to load the merchant dictionary.

## Deploy (Vercel)

Set the project **Root Directory** to `lens`. Add all env vars above (with the prod
`GOOGLE_REDIRECT_URL`). Add `<prod-domain>/auth/callback` to Supabase → Auth → URL
Configuration → Redirect URLs, and enable Google as a provider. Then `vercel --prod`.

Static assets are served by `@vercel/static`; the app runs as one ASGI serverless
function (`api/index.py`). The Postgres connection uses the transaction pooler, which
Vercel can reach (unlike some restrictive local networks).
