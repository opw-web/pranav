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
