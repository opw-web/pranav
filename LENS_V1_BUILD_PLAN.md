# LENS — V1: THE EXPENSE APP THAT SHOWS YOU *WHY*
### Self-contained build document. Paste this entire file as your build/vibe-coding prompt.
### ("LENS" is a working codename — a lens on your money. Rename freely.)

---

## 1. IDEA CONTEXT (read this first)

You are building **LENS** — a modern, cloud, multi-user expense manager whose one job is to make people understand **why** their money moved, not just record where it went. Almost every expense app on the market is a data-entry chore that produces pie charts nobody reads. LENS wins on two things and only two things:

1. **Effortless, delightful input** — adding a transaction, creating a category, and importing a bank file must feel faster and nicer than any competitor. This is the retention engine. People quit finance apps because keeping them current is annoying; if input is painless, they stay.
2. **Deterministic "why" analytics** — a *Spending Detective* that explains what changed and why ("spending rose 25%; the driver was weekend food delivery +₹4,200"), a *what-changed-vs-normal* view, a trustworthy *safe-to-spend* number, and trip/event cost rollups. All computed in code/SQL. **No AI in V1.**

This document is **V1**. It is the foundation: accounts, transactions, categories/tags, import, a rules-based categorizer, recurring detection, reframed budgeting, and the deterministic insight layer. Everything must be rock solid and, above all, **pleasant to type into**, because every later version sits on top of this data and this habit.

### Non-negotiable project rules (apply to everything below)

- **Base language is Python.** All application logic, routing, parsing, analytics, and templating live in Python. The only non-Python code is a thin sprinkle of HTMX/Alpine attributes in HTML and one small `app.js`. No React, no Next.js, no SPA framework.
- **Multi-user cloud app.** Supabase hosts Postgres + Auth. **Google is the only sign-in method in V1.**
- **Row-Level Security (RLS) is mandatory and non-optional.** Every user-scoped table enforces `auth.uid() = user_id`. A user must never be able to read another user's row. This is a security requirement, not a nice-to-have.
- **Every number is computed deterministically** in SQL or Python. There is no LLM, no ML, no "AI-generated" text anywhere in V1. When you see "insight," read it as "a template filled with numbers a query produced."
- **UX is the top priority.** When a design choice trades a little engineering simplicity for a lot less friction in *data entry* or *category creation*, take the friction win. Those two flows are the north star (see §5, the UX Playbook — treat it as spec, not garnish).
- **Serverless-lean.** The app deploys to Vercel as Python serverless functions. Keep dependencies small and cold starts fast. **Do not import pandas in the request path** — do analytics in SQL. (See §2.6.)
- **Currency-aware, INR-default.** Default currency ₹, but store a currency code per account. No multi-currency conversion math in V1 — just don't hardcode the symbol.
- **Free-tier conscious.** It should run comfortably on Supabase + Vercel free tiers for a solo dev and early users. (Verify current free-tier row/storage/bandwidth and function-execution limits before launch — these change.)

### What V1 delivers when done

A signed-in user can: connect via Google; land on a dashboard showing a single trustworthy **safe-to-spend** number plus what changed this month; add a transaction in seconds via a keyboard-first quick-add bar; create categories on the fly without leaving the flow; import a bank CSV through a mapping wizard that remembers the bank next time; have transactions auto-categorized by a rules engine that learns from corrections; see detected recurring payments and upcoming bills; get a **Spending Detective** breakdown of why a period changed; roll up any trip or event by tag ("what did Goa cost?"); and export/back up everything. All fast, all private to that user, all deterministic.

### Product concepts you (the builder) need, in plain language

- **Safe-to-spend** — the one hero number. Roughly: money you can actually spend for the rest of the period without breaking your normal commitments. Formula in §4.4. It is the daily reason to open the app; it must feel *right* or the whole product loses trust.
- **Normal / baseline** — for each category, the typical amount a user spends (e.g. median of the last 3 months). "This month vs normal" is the core comparison that powers the dashboard, budgeting, and the Detective. There is no manual budget required for this — it's derived from history.
- **Spending Detective** — period-over-period **attribution**: compute the deltas per category and per merchant, rank the drivers, and state the top few. The value is the *why* (which categories/merchants drove the change), not the *what* (a total went up).
- **Transfer** — moving your own money between your own accounts (bank → wallet, or a credit-card payment). It must **never** count as an expense or income. Getting this wrong makes every total wrong.
- **Refund** — money back for a prior purchase. It reduces spend in its category; it is not income.
- **Recurring series** — a subscription/bill/EMI that repeats on a cadence. Detected by pattern (same-ish merchant + same-ish amount + regular interval), then **confirmed by the user** — never auto-committed silently.
- **Rules engine (the categorizer)** — since there is no AI, categorization = a shipped merchant dictionary + fuzzy string match + rules the user teaches by correcting. Deterministic, fast, and it *improves per user* because every correction becomes a permanent rule.

---

## 2. ARCHITECTURE

### 2.1 Tech stack (install these exactly)

| Layer | Tool | Install / source |
|-------|------|------------------|
| Language | Python 3.11+ | — |
| Web framework | FastAPI | `pip install fastapi uvicorn` |
| Templating | Jinja2 | `pip install jinja2` |
| Server-driven interactivity | HTMX | vendored in `static/js/htmx.min.js` |
| Sprinkle interactivity | Alpine.js | vendored in `static/js/alpine.min.js` |
| Styling | Tailwind CSS (standalone CLI) | download the standalone binary — **no Node required for the app** |
| Charts (used sparingly) | Chart.js | CDN or vendored |
| DB host + Auth | Supabase (Postgres 15 + Auth) | create a project at supabase.com |
| DB access | SQLAlchemy 2 + asyncpg | `pip install sqlalchemy[asyncio] asyncpg` |
| Supabase SDK (auth verify, storage) | supabase-py | `pip install supabase` |
| Migrations | Alembic (or raw SQL files) | `pip install alembic` |
| CSV encoding detection | charset-normalizer | `pip install charset-normalizer` |
| Flexible date parsing | python-dateutil | `pip install python-dateutil` |
| Fuzzy merchant matching | RapidFuzz (fast, C++) | `pip install rapidfuzz` |
| Validation | Pydantic v2 | comes with FastAPI |
| Env loading | python-dotenv | `pip install python-dotenv` |
| Deploy | Vercel (Python serverless) | `npm i -g vercel` (CLI only) |

**Deliberately NOT installed:** pandas, numpy, any ML/LLM library, any JS SPA framework. If you feel the urge to `pip install pandas`, do the aggregation in SQL instead (§2.6).

**Why this stack fits the goals:** FastAPI + Jinja + HTMX gives an SPA-like feel (inline edits, partial updates, no full-page reloads) while keeping 100% of logic in Python and every interaction as a plain stateless HTTP request — which is exactly what serverless wants. Tailwind's standalone CLI means you never need a Node build for the app itself.

### 2.2 Accounts & keys you need

- A **Supabase project** → gives you a Postgres connection string, a project URL, an `anon` key, and a `service_role` key (server-side only, never shipped to the browser).
- A **Google Cloud OAuth client** (Web application) → Client ID + Secret. Paste these into Supabase → Auth → Providers → Google, and add your Vercel domain + `localhost` to the authorized redirect URLs.
- A **Vercel account** linked to your repo.

### 2.3 Auth flow (Google via Supabase)

1. Browser hits `/login` → button "Continue with Google" → redirects to Supabase's Google OAuth URL.
2. Google → Supabase → redirects back to your `/auth/callback` with a session (access + refresh JWT).
3. Server sets the session tokens in **httpOnly secure cookies**.
4. Every protected request runs a `get_current_user` dependency that verifies the Supabase JWT and extracts `user_id` (= `auth.uid()`). All DB queries are scoped to that id, and RLS enforces it a second time at the database. **Two layers: app filter + RLS.** Never rely on only one.
5. On first-ever login, run **onboarding seed** (§4.6): create starter categories and a default "Cash" account so the app is never an empty void.

### 2.4 Folder structure (create this now)

```
lens/
+-- app/
|   +-- main.py                     # FastAPI app: mounts routers, static, templates, middleware
|   +-- config.py                   # env: SUPABASE_URL, keys, DATABASE_URL, secrets
|   +-- database.py                 # async SQLAlchemy engine + session factory
|   +-- auth/
|   |   +-- routes.py               # /login, /auth/callback, /logout
|   |   +-- session.py              # cookie <-> JWT, verify Supabase token
|   |   +-- deps.py                 # get_current_user dependency
|   +-- models/                     # SQLAlchemy ORM: account, category, tag, transaction, rule, recurring, budget, import_batch
|   +-- schemas/                    # Pydantic request/response models
|   +-- routers/                    # each returns HTML fragments (HTMX) or JSON
|   |   +-- dashboard.py
|   |   +-- transactions.py         # add / edit / delete / list / filter / bulk / quick-add parse
|   |   +-- categories.py           # CRUD + create-on-the-fly + merge/rename
|   |   +-- tags.py
|   |   +-- accounts.py             # CRUD + reconcile
|   |   +-- import_.py              # upload -> map -> preview -> commit (chunked)
|   |   +-- recurring.py            # detected list + confirm + upcoming
|   |   +-- budgets.py              # auto-normal + optional manual
|   |   +-- insights.py             # Detective / what-changed / trip rollups / recap
|   |   +-- rules.py                # view/manage categorization rules
|   |   +-- settings.py             # export / backup / preferences
|   +-- services/
|   |   +-- categorizer.py          # rules engine: seed dict + fuzzy + user rules
|   |   +-- importer.py             # parse, detect header/date/delimiter, dedupe, transfer-match
|   |   +-- recurring_detector.py   # cadence pattern detection
|   |   +-- analytics.py            # SQL-first: safe-to-spend, normals, deltas, diffs
|   |   +-- recap.py                # monthly recap builder (template + numbers)
|   |   +-- reconcile.py            # balance adjustment logic
|   |   +-- quickadd_parser.py      # deterministic parse of the quick-add bar (NOT AI)
|   +-- templates/
|   |   +-- base.html               # shell: nav, quick-add bar, htmx + alpine includes
|   |   +-- dashboard.html
|   |   +-- transactions.html
|   |   +-- import_wizard.html
|   |   +-- categories.html
|   |   +-- accounts.html
|   |   +-- recurring.html
|   |   +-- insights.html
|   |   +-- recap.html
|   |   +-- partials/               # HTMX fragments returned by routers
|   |       +-- txn_row.html
|   |       +-- txn_edit_row.html
|   |       +-- quick_add_result.html
|   |       +-- category_picker.html
|   |       +-- import_preview.html
|   |       +-- toast.html          # includes undo actions
|   +-- static/
|   |   +-- css/app.css             # Tailwind output
|   |   +-- js/htmx.min.js
|   |   +-- js/alpine.min.js
|   |   +-- js/app.js               # keyboard shortcuts, focus management, tiny helpers
|   +-- seeds/
|       +-- merchants_in.csv        # shipped Indian merchant dictionary (pattern -> name, category)
|       +-- categories_default.json # starter category tree
+-- migrations/
|   +-- 001_init.sql                # tables
|   +-- 002_rls.sql                 # RLS policies (CRITICAL)
|   +-- 003_indexes.sql
+-- scripts/
|   +-- build_css.sh                # tailwind standalone build
|   +-- load_merchant_seed.py
+-- tests/
+-- vercel.json                     # Python serverless config
+-- requirements.txt
+-- .env.example
+-- README.md
```

### 2.5 Database schema (run this SQL; adjust types as you like)

> Every user-scoped table has `user_id UUID NOT NULL REFERENCES auth.users(id)`. RLS policies in §2.5.1 are **mandatory**.

```sql
-- ACCOUNTS
CREATE TABLE accounts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    type          TEXT NOT NULL CHECK (type IN ('bank','cash','credit_card','wallet')),
    currency      TEXT NOT NULL DEFAULT 'INR',
    opening_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
    is_spendable  BOOLEAN NOT NULL DEFAULT TRUE,   -- credit_card = FALSE (not part of safe-to-spend cash)
    is_archived   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- CATEGORIES (max 2 levels: a category with parent_id != NULL cannot itself be a parent)
CREATE TABLE categories (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    parent_id     UUID REFERENCES categories(id) ON DELETE SET NULL,
    kind          TEXT NOT NULL DEFAULT 'expense' CHECK (kind IN ('expense','income')),
    color         TEXT,          -- hex; picker suggests a palette
    icon          TEXT,          -- short emoji or icon key
    is_system     BOOLEAN NOT NULL DEFAULT FALSE,  -- seeded starter; still editable
    sort_order    INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, parent_id, name)
);

-- TAGS (cross-cutting: trips, events, work)
CREATE TABLE tags (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    color      TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, name)
);

-- TRANSACTIONS
CREATE TABLE transactions (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    account_id     UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    type           TEXT NOT NULL CHECK (type IN ('expense','income','transfer','refund')),
    amount         NUMERIC(14,2) NOT NULL CHECK (amount >= 0),  -- always positive; type gives sign
    currency       TEXT NOT NULL DEFAULT 'INR',
    txn_date       DATE NOT NULL,
    txn_time       TIME,
    merchant_raw   TEXT,          -- ORIGINAL string from import, e.g. 'AMZN MKTP 48293' (never overwrite)
    merchant_clean TEXT,          -- cleaned display name, e.g. 'Amazon'
    category_id    UUID REFERENCES categories(id) ON DELETE SET NULL,  -- NULL = Uncategorized (allowed!)
    notes          TEXT,
    -- transfer linkage: a transfer is stored as ONE row with the counter-account set
    transfer_account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    transfer_group_id   UUID,     -- links the two legs if you store both legs
    is_reimbursable BOOLEAN NOT NULL DEFAULT FALSE,
    is_pending      BOOLEAN NOT NULL DEFAULT FALSE,
    source          TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual','import','quickadd','recurring')),
    import_batch_id UUID,
    dedupe_hash     TEXT,         -- hash(account_id,txn_date,amount,merchant_raw) for import dedupe
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,  -- soft delete so UNDO works
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE transaction_tags (
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    tag_id         UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (transaction_id, tag_id)
);

-- CATEGORIZATION RULES (user-taught + seeded). This is "the AI", deterministically.
CREATE TABLE categorization_rules (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    match_type    TEXT NOT NULL CHECK (match_type IN ('contains','exact','regex')),
    pattern       TEXT NOT NULL,               -- matched against merchant_raw (case-insensitive)
    set_merchant  TEXT,                         -- optional cleaned name to apply
    set_category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    priority      INT NOT NULL DEFAULT 100,     -- lower runs first; user rules beat seed
    times_applied INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- SHIPPED MERCHANT DICTIONARY (global, read-only seed; not user-scoped)
CREATE TABLE merchant_seed (
    id             BIGSERIAL PRIMARY KEY,
    pattern        TEXT NOT NULL,     -- e.g. 'swiggy'
    merchant_clean TEXT NOT NULL,     -- e.g. 'Swiggy'
    category_key   TEXT NOT NULL      -- e.g. 'food.restaurants' -> mapped to user's category on apply
);

-- RECURRING SERIES
CREATE TABLE recurring_series (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    merchant_clean TEXT NOT NULL,
    account_id     UUID REFERENCES accounts(id) ON DELETE SET NULL,
    category_id    UUID REFERENCES categories(id) ON DELETE SET NULL,
    expected_amount NUMERIC(14,2),
    amount_tolerance NUMERIC(6,2) NOT NULL DEFAULT 0.15,  -- ±15%
    cadence        TEXT NOT NULL CHECK (cadence IN ('weekly','monthly','yearly','custom')),
    next_due_date  DATE,
    last_seen_date DATE,
    status         TEXT NOT NULL DEFAULT 'detected' CHECK (status IN ('detected','active','paused')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- BUDGETS (optional manual; NULL amount = "use auto-derived normal")
CREATE TABLE budgets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,  -- NULL = overall
    period      TEXT NOT NULL DEFAULT 'monthly',
    amount      NUMERIC(14,2),        -- NULL => derive from history
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- IMPORT BATCHES + REMEMBERED COLUMN MAPPINGS
CREATE TABLE import_batches (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    account_id    UUID REFERENCES accounts(id) ON DELETE SET NULL,
    filename      TEXT,
    row_count     INT DEFAULT 0,
    imported_count INT DEFAULT 0,
    skipped_count INT DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE column_mappings (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    bank_signature TEXT NOT NULL,   -- hash of the normalized header row
    mapping        JSONB NOT NULL,  -- {"date":"Txn Date","amount":"Amount","desc":"Narration",...}
    date_format    TEXT,            -- e.g. '%d/%m/%Y'
    amount_convention TEXT,         -- 'signed' | 'debit_credit_columns'
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, bank_signature)
);

-- CACHED MONTHLY RECAP
CREATE TABLE monthly_recaps (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    period     TEXT NOT NULL,       -- 'YYYY-MM'
    stats      JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, period)
);
```

Indexes (003_indexes.sql):
```sql
CREATE INDEX idx_txn_user_date   ON transactions (user_id, txn_date DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_txn_user_cat    ON transactions (user_id, category_id)   WHERE is_deleted = FALSE;
CREATE INDEX idx_txn_dedupe      ON transactions (user_id, dedupe_hash);
CREATE INDEX idx_txn_merchant    ON transactions (user_id, merchant_clean);
CREATE INDEX idx_rules_user      ON categorization_rules (user_id, priority);
CREATE INDEX idx_merchant_seed   ON merchant_seed (pattern);
```

#### 2.5.1 RLS policies (MANDATORY — do not skip)

```sql
ALTER TABLE accounts             ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories           ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions         ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_tags     ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorization_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_series     ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets              ENABLE ROW LEVEL SECURITY;
ALTER TABLE import_batches       ENABLE ROW LEVEL SECURITY;
ALTER TABLE column_mappings      ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_recaps       ENABLE ROW LEVEL SECURITY;

-- Pattern, repeated per user-scoped table (example for transactions):
CREATE POLICY txn_select ON transactions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY txn_insert ON transactions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY txn_update ON transactions FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY txn_delete ON transactions FOR DELETE USING (auth.uid() = user_id);

-- merchant_seed is global read-only:
ALTER TABLE merchant_seed ENABLE ROW LEVEL SECURITY;
CREATE POLICY seed_read ON merchant_seed FOR SELECT USING (true);
```
> For `transaction_tags` (no `user_id` column), scope via the parent transaction:
> `USING (EXISTS (SELECT 1 FROM transactions t WHERE t.id = transaction_id AND t.user_id = auth.uid()))`.

### 2.6 The SQL-first analytics rule (why no pandas)

The Detective, normals, safe-to-spend, and the diff view are all **aggregations**, and Postgres does aggregations better and faster than a pandas dataframe you'd have to cold-start on every serverless call. So:

- **Do it in SQL** — `GROUP BY`, `SUM`, window functions, `PERCENTILE_CONT` for medians, `LAG` for period-over-period.
- Keep Python for *orchestration and templating* of those results, not number-crunching.
- This keeps the deploy bundle tiny (fast cold starts) and the analytics correct (one source of truth in the DB).

Example — Detective category deltas for a month vs the prior month:
```sql
WITH cur AS (
  SELECT category_id, SUM(amount) AS spend
  FROM transactions
  WHERE user_id = :uid AND type = 'expense' AND is_deleted = FALSE
    AND txn_date >= :cur_start AND txn_date < :cur_end
  GROUP BY category_id
),
prev AS (
  SELECT category_id, SUM(amount) AS spend
  FROM transactions
  WHERE user_id = :uid AND type = 'expense' AND is_deleted = FALSE
    AND txn_date >= :prev_start AND txn_date < :prev_end
  GROUP BY category_id
)
SELECT COALESCE(cur.category_id, prev.category_id) AS category_id,
       COALESCE(cur.spend,0) AS cur_spend,
       COALESCE(prev.spend,0) AS prev_spend,
       COALESCE(cur.spend,0) - COALESCE(prev.spend,0) AS delta
FROM cur FULL OUTER JOIN prev USING (category_id)
ORDER BY delta DESC;   -- top rows = the "why"
```

### 2.7 Deployment notes (Vercel + serverless reality)

- FastAPI runs on Vercel as a Python serverless function via an ASGI entrypoint + `vercel.json` routing all paths to it. Verify the current Python runtime version and the **function execution-time limit** for your Vercel plan before relying on it — these numbers change.
- **Cold starts are real.** Every avoided dependency helps. This is the concrete reason pandas is banned from the request path.
- **Imports must be chunked** so no single request runs long: upload the file once, then process **N rows per request** (e.g. 200), paginating server-side, showing a progress bar via HTMX. This keeps every request well under the limit and gives the user live feedback. (See §5.3.)
- Static files (`htmx.min.js`, `alpine.min.js`, Tailwind output) are served as static assets, not through the function.
- Secrets (`service_role` key, DB URL) are Vercel environment variables, never in client code.

> Honest flag carried from earlier: Python is a second-class citizen on Vercel (it's built for Node/Next). The FastAPI+HTMX pattern deploys fine because it's stateless request/response, but if you hit friction, the same codebase runs unchanged on Railway/Render/Fly with a persistent process and no cold starts. Keep that as a fallback host; nothing in the design depends on Vercel specifically.

---

## 3. GOALS

1. **Painless input.** Adding a transaction takes seconds and few keystrokes; creating a category never interrupts the flow; importing a bank file is a guided wizard that gets smarter each time.
2. **Trustworthy safe-to-spend.** One hero number the user believes, because transfers/refunds are handled correctly and the math is transparent.
3. **The "why".** A deterministic Spending Detective and what-changed view that explain movements, not just totals.
4. **A categorizer that learns.** Rules engine that starts useful (shipped dictionary) and gets personal (user corrections become permanent rules).
5. **Rock-solid multi-user isolation.** RLS-enforced; no user can ever see another's data.
6. **Runs on free tiers**, all logic in Python, ready to extend in V2.

---

## 4. REQUIREMENTS

### 4.1 The categorizer (services/categorizer.py) — deterministic, learns from corrections

`categorize(merchant_raw, user_id) -> (merchant_clean, category_id, confidence)`:

1. **User rules first.** Check `categorization_rules` for this user, by `priority`. `contains`/`exact`/`regex` match against `merchant_raw` (case-insensitive). First hit wins → high confidence. Increment `times_applied`.
2. **Shipped dictionary.** Fuzzy-match `merchant_raw` against `merchant_seed.pattern` with RapidFuzz (token-set ratio). Above a threshold (e.g. 88) → apply `merchant_clean` + mapped category → medium/high confidence.
3. **Miss → Uncategorized.** Return `None` category with low confidence. **Never guess wildly.** Uncategorized is a valid, honest state.
4. **Learning:** when the user recategorizes a transaction, offer (default-on) "Always categorize *[merchant]* as *[category]*?" → creates a `categorization_rules` row. Next time it's deterministic. Optionally back-apply to existing matching uncategorized transactions (ask first).

Seed data: ship `merchants_in.csv` with the common Indian merchants (Swiggy, Zomato, Uber, Ola, Amazon, Flipkart, BigBasket, Blinkit, Zepto, Jio, Airtel, Netflix, Spotify, BSES/electricity, common banks/UPI patterns…). This is what makes the *first* import feel smart with zero AI.

### 4.2 The importer (services/importer.py)

- **Detect:** encoding (charset-normalizer), delimiter, header row, date format (python-dateutil), and amount convention (single signed column vs separate debit/credit columns).
- **Map:** guess column roles from header names; let the user confirm/adjust in the wizard (§5.3). Save the mapping keyed by `bank_signature` so the **second import from that bank is one click**.
- **Dedupe:** compute `dedupe_hash = hash(account_id, txn_date, amount, merchant_raw)`; skip rows already present. Re-importing the same file must add **zero** duplicates.
- **Transfer detection:** if two imported rows across two accounts have opposite amounts, same/adjacent date, and matching magnitude → propose linking them as a single **transfer** (so they don't count as expense+income).
- **Categorize on import:** run each row through the categorizer; only the uncategorized/low-confidence rows go into a focused review queue — the user never re-touches the confident ones.
- **Commit atomically per batch**, chunked (§2.7), with a summary: imported / skipped(dupes) / needs-review.

### 4.3 Recurring detection (services/recurring_detector.py)

- Group historical transactions by `merchant_clean`; within a group, look for a **regular interval** (≈30d monthly, ≈7d weekly, ≈365d yearly) and a **stable amount** (within tolerance).
- Emit `recurring_series` rows with `status='detected'`. **Surface for confirmation; never auto-activate.**
- On confirm, compute `next_due_date`; the dashboard shows upcoming dues; a scheduled function (Vercel Cron) sends reminders and flags "renewed higher than usual".

### 4.4 Analytics (services/analytics.py) — all SQL-first

**Normals (baseline per category):** median of the last 3 full calendar months of expense per category (`PERCENTILE_CONT(0.5)`). Recomputed on read or cached daily.

**Safe-to-spend (the hero number)** — V1 formula (state assumptions in the UI so it's trustworthy):
```
spendable_balance     = sum(current balance of accounts where is_spendable = TRUE)
upcoming_committed    = sum(confirmed recurring_series due between today and period_end)
essential_remaining   = max(0, essential_normal_for_period − essential_spent_so_far)
safe_to_spend         = spendable_balance − upcoming_committed − essential_remaining
```
where `current balance = opening_balance + income + refunds − expense ± transfers` for that account, and "essential" = a flag/set of categories (Rent, Bills, Groceries, Health…). Show the breakdown on tap — never a naked number. Tune definitions with real usage.

**Spending Detective (`why`):** the delta query in §2.6, run at category level and merchant level, returning the top N drivers of an increase or decrease, phrased by a **template** ("Restaurants +₹4,200 · Shopping +₹8,000 drove a 25% rise vs last month"). No prose generation — slot numbers into fixed sentences.

**What-changed-vs-normal (diff view):** new merchants this period, dropped merchants, categories above/below normal, newly detected recurring charges, a subscription that renewed higher.

**Trip/event rollup:** `SUM(amount) ... WHERE tag = :tag GROUP BY category` → "Goa: ₹18,400 total — Travel ₹9k, Food ₹5k, Stay ₹4.4k."

### 4.5 Routes (HTMX-first; most return HTML fragments, some JSON)

```
GET  /                              -> dashboard
POST /txn/quickadd                  -> parse quick-add bar, create txn, return new row fragment + toast
GET  /txn                           -> transaction list (filters as query params)
POST /txn                           -> create (form)
GET  /txn/{id}/edit                 -> inline edit-row fragment
PATCH/txn/{id}                      -> update field(s), return updated row fragment
DELETE /txn/{id}                    -> soft-delete, return toast with UNDO
POST /txn/{id}/undo                 -> restore
POST /txn/bulk                      -> bulk set category/tag/delete
GET  /categories                    -> manage page
POST /categories                    -> create (also called inline from picker) -> return picker option
POST /categories/merge              -> merge A into B, reassign txns
GET  /category-picker?q=            -> searchable picker fragment (with "Create '<q>'")
GET  /accounts                      -> list + balances
POST /accounts/{id}/reconcile       -> create adjustment txn
POST /import/upload                 -> receive file, detect, return mapping wizard
POST /import/preview                -> apply mapping, return preview + dedupe/transfer flags
POST /import/commit                 -> chunked commit (page param), return progress fragment
GET  /recurring                     -> detected + confirmed + upcoming
POST /recurring/{id}/confirm        -> activate series
GET  /insights                      -> Detective + diff + trip rollups
GET  /recap/{period}                -> monthly recap
GET  /settings/export               -> download full CSV/JSON backup
GET  /login  /auth/callback  /logout
GET  /healthz
```

### 4.6 First-run onboarding (services on first login)

- Seed a **starter category tree** from `categories_default.json` (Food › Restaurants/Groceries/Coffee, Transport, Shopping, Entertainment, Health, Travel, Bills, Income…). All `is_system=TRUE` but fully editable.
- Create a default **"Cash"** account.
- Land the user on a friendly empty-state dashboard with two clear calls to action: **"Import a bank statement"** and **"Add your first transaction"**. Never show a blank grid.

---

## 5. THE UX PLAYBOOK (this is the product — treat as spec)

The whole bet is that input and category management feel better here than anywhere else. These three flows get disproportionate design effort.

### 5.1 Data entry — the keyboard-first Quick-Add bar

A single text bar pinned in the top nav on every page, focusable with a global shortcut (e.g. `a`). It accepts natural shorthand and parses it **deterministically** (this is pattern-matching, not AI):

- `450 swiggy lunch` → amount **450**, merchant **swiggy** (→ categorizer → **Food › Restaurants**), note "lunch".
- Tokens: a bare number = amount; `@hdfc` = account; `#goa` = tag; `!food` or `>groceries` = force category; date words `today`/`yesterday`/`12 jul` = date; `+` prefix = income (`+50000 salary`).
- As the user types, show a **live parsed preview** ("₹450 · Swiggy · Food › Restaurants · today · Cash") so there's no guessing.
- **Enter** commits and the new row animates into the list (HTMX swap) with an **Undo** toast. Focus returns to the bar for rapid multi-entry.

Supporting rules for entry everywhere:
- **Smart defaults:** date = today, account = last used, category = categorizer's guess (editable in one keystroke).
- **Inline table editing:** click any cell in the transaction list → it becomes editable → `PATCH` on blur/Enter → no page reload.
- **Bulk actions:** shift-select rows → set category/tag or delete in one action (essential after imports).
- **Duplicate guard:** on add, if a near-identical txn exists (same amount + merchant + day), warn inline (don't block).
- **Undo everywhere:** deletes are soft; every destructive action shows a toast with Undo for ~8s.
- **Full keyboard map:** `a` add, `/` search, `j/k` move, `e` edit, `c` set category, `t` tag, `x` select, `u` undo. Show a `?` cheatsheet.

**Why:** data entry is the single biggest churn driver in this category. Sub-5-second, keyboard-only entry with a live preview is the feature that makes people stay.

### 5.2 Category creation — never leave the flow

- **Create-on-the-fly:** the category picker is a searchable dropdown. Type a name that doesn't exist → the top row becomes **"➕ Create 'Late-night snacks'"**. One click creates it (via `POST /categories`) and selects it, without leaving the transaction. This is the single most important category-UX decision — no "go to Settings to make a category" ever.
- **2 levels only, enforced.** Picker shows parents with indented children; enforce max depth in code so users can't build confusing 4-level trees. Fewer, clearer categories beat a sprawling tree.
- **Recent & frequent on top** of the picker; fuzzy search across all.
- **Color + icon** chosen inline with a small suggested palette (auto-assign a sensible default so the user *can* skip it).
- **Merge & rename without data loss:** renaming updates in place; merging A→B reassigns all A's transactions to B, then deletes A. History stays intact.
- **"Uncategorized" is first-class,** filterable, and there's a **bulk-categorize queue** ("18 uncategorized — assign quickly") so users are never forced to categorize mid-entry.

**Why:** category friction is where tracking dies. If making and picking categories is instant and forgiving, people actually keep their data clean — which is what makes every insight downstream correct.

### 5.3 Import — a wizard that gets smarter each time

1. **Drop a CSV.** Auto-detect encoding, delimiter, header row, date format, amount convention. Pick the target account (or create one inline).
2. **Mapping step** with a **live preview table**: guessed column roles pre-filled (Date, Amount, Description, maybe Debit/Credit). User fixes anything wrong; the preview updates instantly.
3. **Remember the bank.** Save the mapping by `bank_signature`; next import from that bank **skips straight to preview** ("Recognized HDFC format ✓").
4. **Preview & flags:** show what will import, mark **duplicates** (will skip) and detected **transfers** (will link, not double-count).
5. **Auto-categorize** during import; route only the uncategorized/low-confidence rows to a **focused review queue** — the confident majority is never touched.
6. **Chunked commit** with a progress bar (§2.7). End on a clear summary: *"Imported 212 · Skipped 14 duplicates · 9 need a category."* with a one-click jump to that review queue.

**Why:** import is the onboarding *and* the ongoing top-up. If the first import is smooth and the second is one click, the app becomes effortless to keep current — the entire retention thesis in one flow.

### 5.4 Dashboard — one number, then support

- **Hero: safe-to-spend** for the rest of the period, big, with a tap-to-see breakdown (never a naked figure).
- **This month vs your normal** — a compact bar with the templated Detective callout ("Food ₹4,200 above normal").
- **Upcoming committed payments** (confirmed recurring) that threaten the number.
- **Recent activity** (last few txns, inline-editable).
- **One "what changed" card** linking to the full diff view. Deliberately few tiles. The anti-goal is looking like accounting software.

---

## 6. TASKS (build in this order)

1. Create the Supabase project. Run `001_init.sql`, `002_rls.sql`, `003_indexes.sql`. Load `merchant_seed` via `scripts/load_merchant_seed.py`.
2. Scaffold the folder structure. Get FastAPI serving `base.html` with Tailwind + HTMX + Alpine wired.
3. Build **auth**: Google via Supabase, cookie session, `get_current_user`, protected routes, first-run onboarding seed (§4.6). **Verify RLS with two real Google accounts before building anything else.**
4. Build **accounts** CRUD + balance computation.
5. Build **categories**: model, manage page, and the **create-on-the-fly picker** (§5.2) — build the picker early; everything else uses it.
6. Build **transactions**: list, inline edit, delete+undo, bulk actions.
7. Build the **Quick-Add bar + deterministic parser** (§5.1). This is the marquee input flow — polish it.
8. Build the **categorizer** (seed + fuzzy + user rules) and correction-learning.
9. Build the **import wizard** (detect → map → remember → preview → dedupe/transfer → chunked commit → review queue). Test with 2–3 real Indian bank CSVs.
10. Build **recurring detection** + confirm + upcoming, and the Vercel Cron reminder.
11. Build **analytics** in SQL: normals, safe-to-spend, Detective, diff, trip rollups.
12. Build the **dashboard** (§5.4), the **insights** page, the **monthly recap**, and **export/backup**.
13. Run the §7 evaluation. Deploy to Vercel; re-run the deploy-sensitive checks (RLS, cold start, import timing) in production.

---

## 7. DEVELOPER EVALUATION CHECKLIST (beginner-friendly — follow every step)

Work through these after the build. Each says what it means, why it matters, how to verify, and pass/fail.

#### Check 1: RLS actually isolates users (do this FIRST — it's a security check)
- **What / why:** two users must never see each other's data. A bug here is a data breach, not a glitch.
- **How:** sign in as User A, add a transaction; note its id. Sign in as User B and try to fetch it directly (`GET /txn/{id}`) and via a raw Supabase query with B's token.
- **Pass:** B gets nothing (404/empty) both ways. **Fail:** B sees A's row → your RLS policies aren't enabled on every table or a query bypasses `user_id`. Stop and fix before anything else.

#### Check 2: Transfers never count as spending
- **What / why:** moving ₹5,000 bank→wallet must not appear as ₹5,000 expense (and a credit-card payment isn't spending).
- **How:** record a transfer between two accounts. Check the month's total expense and income, and each account balance.
- **Pass:** totals unchanged by the transfer; both balances move correctly. **Fail:** expense or income jumped → your aggregation isn't excluding `type='transfer'`.

#### Check 3: Refunds reduce the right category
- **How:** add a ₹2,000 Shopping expense, then a ₹2,000 refund tagged to Shopping.
- **Pass:** Shopping net for the period ≈ ₹0; refund isn't counted as income. **Fail:** refund shows as income or leaves Shopping at ₹2,000.

#### Check 4: Quick-add is genuinely fast
- **How:** from anywhere, press `a`, type `450 swiggy lunch`, Enter. Time it and count keystrokes.
- **Pass:** transaction created, correctly parsed (₹450 · Swiggy · Food · today), in well under 5 seconds with no mouse. **Fail:** needed the mouse, a reload, or misparsed the amount/merchant.

#### Check 5: Create-a-category-on-the-fly works
- **How:** while adding a transaction, open the category picker and type a brand-new name.
- **Pass:** "➕ Create '…'" appears, one click creates + selects it, and you're still in the same transaction. **Fail:** you had to leave for Settings, or the flow reloaded and lost your entry.

#### Check 6: Import mapping is remembered
- **How:** import a bank CSV (map its columns). Import a second file from the **same** bank.
- **Pass:** the second import recognizes the format and skips straight to preview. **Fail:** it asks you to map columns again → `bank_signature`/`column_mappings` not saving or not matching.

#### Check 7: Import dedupe
- **How:** import the exact same CSV twice.
- **Pass:** the second run imports **0** new rows and reports them as skipped duplicates. **Fail:** duplicates appear → check the `dedupe_hash` inputs.

#### Check 8: The categorizer learns
- **How:** find an uncategorized merchant, recategorize it, accept "always categorize as…". Import/add another transaction from that merchant.
- **Pass:** it's categorized automatically next time. **Fail:** still uncategorized → the correction isn't creating a `categorization_rules` row, or rules aren't checked first.

#### Check 9: Safe-to-spend math is correct (hand-compute once)
- **How:** on a test account, compute by hand: spendable balance − upcoming confirmed recurring − remaining essential normal. Compare to the dashboard.
- **Pass:** matches within rounding, and the on-tap breakdown shows the same components. **Fail:** re-check which account types are `is_spendable`, and that transfers/refunds are handled.

#### Check 10: The Detective points at the real driver
- **How:** in test data, deliberately spike one category this month vs last. Open Insights.
- **Pass:** that category/merchant is named as the top driver, with the right delta. **Fail:** wrong driver or wrong number → check the delta SQL (§2.6) and the period boundaries.

#### Check 11: Trip rollup is correct
- **How:** tag several transactions `#goa`, sum them by hand.
- **Pass:** the Goa rollup total and per-category split match your manual sum. **Fail:** check the tag join and that transfers are excluded.

#### Check 12: Balances reconcile
- **How:** for one account, compute `opening + income + refunds − expense ± transfers` by hand; compare to the shown balance. Then run a reconciliation to a different "actual" number.
- **Pass:** computed balance matches; reconciliation creates a visible adjustment transaction. **Fail:** silent balance drift → your balance query is missing a transaction type.

#### Check 13: Import stays within serverless limits
- **How:** import a large file (e.g. 1,000+ rows) on the deployed Vercel app.
- **Pass:** it completes via chunked requests with a progress bar; no single request times out. **Fail:** one long request → you're not paginating the commit (§2.7).

#### Check 14: Cold start is acceptable
- **How:** hit the deployed app after it's been idle.
- **Pass:** first response is reasonably quick (lean deps paying off). **Fail:** multi-second cold start → check you didn't pull in pandas/numpy or other heavy libs into the request path.

#### Check 15: Export round-trips (backup integrity)
- **How:** export the full CSV/JSON backup; inspect it.
- **Pass:** every transaction, with category/tag/account names, is present and re-importable. **Fail:** missing fields → your export query is thin; a backup you can't restore isn't a backup.

#### Check 16: Timezone / date correctness
- **How:** add a transaction late at night; check the date shown vs stored.
- **Pass:** the date matches the user's local day, consistently. **Fail:** off-by-one dates → standardize: store `txn_date` as the user's local date; store timestamps as `TIMESTAMPTZ` and convert at the edge only.

#### Check 17: First-run is never a blank void
- **How:** sign in with a brand-new Google account.
- **Pass:** starter categories + a Cash account exist, and the dashboard shows clear "Import" / "Add first transaction" actions. **Fail:** empty grids and no guidance → onboarding seed (§4.6) didn't run.

---

## 8. V1 GOAL (definition of done)

A deployed, multi-user web app where a person signs in with Google and, within their first session, imports a bank statement through a wizard that auto-categorizes most of it, adds a transaction in seconds via a keyboard-first quick-add bar, creates a category without leaving the flow, and sees a single trustworthy **safe-to-spend** number plus a plain-language, deterministically-computed explanation of **why** this month differs from their normal — with transfers and refunds handled correctly, every user's data isolated by RLS, all logic in Python, analytics in SQL, and the whole thing running on free-tier Supabase + Vercel. No AI, no bank sync, no accounting-software feel — just the fastest, friendliest way to put money data in, and the clearest explanation of what it means coming out.
