# Graph Report - .  (2026-07-07)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 416 nodes · 609 edges · 78 communities (25 shown, 53 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 70 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4ed6cefc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Safe-to-Spend Core Concepts|Safe-to-Spend Core Concepts]]
- [[_COMMUNITY_Graphify Setup Pipeline|Graphify Setup Pipeline]]
- [[_COMMUNITY_Auth, DB & Security Foundation|Auth, DB & Security Foundation]]
- [[_COMMUNITY_Web Stack (FastAPIHTMXAlpine)|Web Stack (FastAPI/HTMX/Alpine)]]
- [[_COMMUNITY_Categorization Rules Engine|Categorization Rules Engine]]
- [[_COMMUNITY_Import & Transfer Handling|Import & Transfer Handling]]
- [[_COMMUNITY_Recurring Transaction Detection|Recurring Transaction Detection]]
- [[_COMMUNITY_Category Picker UX|Category Picker UX]]
- [[_COMMUNITY_Build Script Entry Point|Build Script Entry Point]]
- [[_COMMUNITY_Database Schema & Architecture|Database Schema & Architecture]]
- [[_COMMUNITY_Backend Service Requirements|Backend Service Requirements]]
- [[_COMMUNITY_Refresh Hook Scripts|Refresh Hook Scripts]]
- [[_COMMUNITY_UX Playbook Spec|UX Playbook Spec]]
- [[_COMMUNITY_transactions.py|transactions.py]]
- [[_COMMUNITY_Project Instructions|Project Instructions]]
- [[_COMMUNITY_Graphify Project Setup|Graphify Project Setup]]
- [[_COMMUNITY_Serial Graph Build Script|Serial Graph Build Script]]
- [[_COMMUNITY_Community Labeling Backend|Community Labeling Backend]]
- [[_COMMUNITY_Graphify Ignore Rules|Graphify Ignore Rules]]
- [[_COMMUNITY_Obsidian Vault Builder|Obsidian Vault Builder]]
- [[_COMMUNITY_No-Backup Environment Flag|No-Backup Environment Flag]]
- [[_COMMUNITY_Auto-Refresh Hook Registration|Auto-Refresh Hook Registration]]
- [[_COMMUNITY_Consult-Graph Hook|Consult-Graph Hook]]
- [[_COMMUNITY_Refresh Hook Script|Refresh Hook Script]]
- [[_COMMUNITY_macOS AST Extraction Crash|macOS AST Extraction Crash]]
- [[_COMMUNITY_Analytics Service|Analytics Service]]
- [[_COMMUNITY_Categorizer Service|Categorizer Service]]
- [[_COMMUNITY_Create-on-the-Fly Category Picker|Create-on-the-Fly Category Picker]]
- [[_COMMUNITY_Column Mappings Table|Column Mappings Table]]
- [[_COMMUNITY_Dashboard Hero Number|Dashboard Hero Number]]
- [[_COMMUNITY_Delightful Input Design|Delightful Input Design]]
- [[_COMMUNITY_Developer Evaluation Checklist|Developer Evaluation Checklist]]
- [[_COMMUNITY_FastAPI Framework|FastAPI Framework]]
- [[_COMMUNITY_App Folder Structure|App Folder Structure]]
- [[_COMMUNITY_Google OAuth via Supabase|Google OAuth via Supabase]]
- [[_COMMUNITY_HTMX|HTMX]]
- [[_COMMUNITY_Bank CSV Import Wizard|Bank CSV Import Wizard]]
- [[_COMMUNITY_Importer Service|Importer Service]]
- [[_COMMUNITY_Jinja2 Templating|Jinja2 Templating]]
- [[_COMMUNITY_LENS Expense App|LENS Expense App]]
- [[_COMMUNITY_SQL-First Analytics|SQL-First Analytics]]
- [[_COMMUNITY_Baseline Spending|Baseline Spending]]
- [[_COMMUNITY_Keyboard-First Quick-Add Bar|Keyboard-First Quick-Add Bar]]
- [[_COMMUNITY_Quick-Add Parser|Quick-Add Parser]]
- [[_COMMUNITY_RapidFuzz Fuzzy Matching|RapidFuzz Fuzzy Matching]]
- [[_COMMUNITY_Recurring Series Detection|Recurring Series Detection]]
- [[_COMMUNITY_Recurring Series Table|Recurring Series Table]]
- [[_COMMUNITY_Refund Transaction Type|Refund Transaction Type]]
- [[_COMMUNITY_Row-Level Security|Row-Level Security]]
- [[_COMMUNITY_Categorization Rules Engine|Categorization Rules Engine]]
- [[_COMMUNITY_Safe-to-Spend Number|Safe-to-Spend Number]]
- [[_COMMUNITY_Spending Detective|Spending Detective]]
- [[_COMMUNITY_SQLAlchemy + asyncpg|SQLAlchemy + asyncpg]]
- [[_COMMUNITY_Supabase Postgres & Auth|Supabase Postgres & Auth]]
- [[_COMMUNITY_Tailwind CSS|Tailwind CSS]]
- [[_COMMUNITY_Transactions Table|Transactions Table]]
- [[_COMMUNITY_Transfer Transaction Type|Transfer Transaction Type]]
- [[_COMMUNITY_Vercel Serverless Deployment|Vercel Serverless Deployment]]
- [[_COMMUNITY_Merchant Seed Loader|Merchant Seed Loader]]
- [[_COMMUNITY_App Entrypoint & Healthcheck|App Entrypoint & Healthcheck]]
- [[_COMMUNITY_CSS Build Script|CSS Build Script]]
- [[_COMMUNITY_App Entry Point|App Entry Point]]
- [[_COMMUNITY_session.py|session.py]]
- [[_COMMUNITY_routes.py|routes.py]]
- [[_COMMUNITY_main.py|main.py]]
- [[_COMMUNITY_CurrentUser|CurrentUser]]
- [[_COMMUNITY_quickadd_parser.py|quickadd_parser.py]]
- [[_COMMUNITY_importer.py|importer.py]]
- [[_COMMUNITY_session.py|session.py]]
- [[_COMMUNITY_test_importer.py|test_importer.py]]
- [[_COMMUNITY_detect_series_for_merchant|detect_series_for_merchant]]
- [[_COMMUNITY_confirm|confirm]]
- [[_COMMUNITY_test_recurring.py|test_recurring.py]]

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 34 edges
2. `7. DEVELOPER EVALUATION CHECKLIST (beginner-friendly — follow every step)` - 18 edges
3. `get_grouped_tree()` - 13 edges
4. `build_quickadd_preview()` - 11 edges
5. `LENS — V1: THE EXPENSE APP THAT SHOWS YOU *WHY*` - 11 edges
6. `get_account_balances()` - 10 edges
7. `analyze()` - 10 edges
8. `create_txn()` - 9 edges
9. `patch_txn()` - 9 edges
10. `bulk_action()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Account` --uses--> `Base`  [INFERRED]
  lens/app/models/account.py → lens/app/models/base.py
- `Category` --uses--> `Base`  [INFERRED]
  lens/app/models/category.py → lens/app/models/base.py
- `Tag` --uses--> `Base`  [INFERRED]
  lens/app/models/tag.py → lens/app/models/base.py
- `Transaction` --uses--> `Base`  [INFERRED]
  lens/app/models/transaction.py → lens/app/models/base.py
- `upload()` --calls--> `recall_column_mapping()`  [INFERRED]
  lens/app/routers/import_.py → lens/app/services/import_commit.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Deterministic-Only Analytics Pattern (No AI/ML)** — lens_v1_build_plan_rules_engine, lens_v1_build_plan_spending_detective, lens_v1_build_plan_analytics_service, lens_v1_build_plan_no_pandas_rule [INFERRED 0.85]
- **Money-Movement Semantics (Transfer/Refund/Safe-to-Spend)** — lens_v1_build_plan_transfer, lens_v1_build_plan_refund, lens_v1_build_plan_safe_to_spend, lens_v1_build_plan_transactions_table [INFERRED 0.85]
- **Graphify Auto-Refresh Pipeline** — graphify_setup_prompt_posttooluse_hook, graphify_setup_prompt_refresh_sh, graphify_setup_prompt_make_vault_py, graphify_setup_prompt_community_labeling [EXTRACTED 1.00]

## Communities (78 total, 53 thin omitted)

### Community 0 - "Safe-to-Spend Core Concepts"
Cohesion: 0.06
Nodes (31): 1. IDEA CONTEXT (read this first), 2.1 Tech stack (install these exactly), 2.2 Accounts & keys you need, 2.3 Auth flow (Google via Supabase), 2.4 Folder structure (create this now), 2.5.1 RLS policies (MANDATORY — do not skip), 2.5 Database schema (run this SQL; adjust types as you like), 2.6 The SQL-first analytics rule (why no pandas) (+23 more)

### Community 8 - "Build Script Entry Point"
Cohesion: 0.11
Nodes (18): 7. DEVELOPER EVALUATION CHECKLIST (beginner-friendly — follow every step), Check 10: The Detective points at the real driver, Check 11: Trip rollup is correct, Check 12: Balances reconcile, Check 13: Import stays within serverless limits, Check 14: Cold start is acceptable, Check 15: Export round-trips (backup integrity), Check 16: Timezone / date correctness (+10 more)

### Community 9 - "Database Schema & Architecture"
Cohesion: 0.16
Nodes (19): delete_rule(), learn(), AsyncSession, Request, Called when the user accepts 'Always categorize <merchant> as <category>?'., rules_page(), _rules_with_names(), back_apply_rule() (+11 more)

### Community 10 - "Backend Service Requirements"
Cohesion: 0.20
Nodes (22): categories_page(), category_picker(), create_category_route(), delete_category_route(), merge_categories_route(), AsyncSession, Request, rename_category_route() (+14 more)

### Community 11 - "Refresh Hook Scripts"
Cohesion: 0.40
Nodes (3): GRAPHIFY_NO_BACKUP, OBJC_DISABLE_INITIALIZE_FORK_SAFETY, refresh.sh script

### Community 12 - "UX Playbook Spec"
Cohesion: 0.23
Nodes (14): archive_account(), create_account(), list_accounts(), AsyncSession, Request, reconcile(), rename_account(), get_account_balances() (+6 more)

### Community 13 - "transactions.py"
Cohesion: 0.23
Nodes (19): category_normals(), _deltas(), _essential_category_ids(), last_n_full_months(), month_bounds(), prev_month_bounds(), AsyncSession, date (+11 more)

### Community 59 - "Merchant Seed Loader"
Cohesion: 0.67
Nodes (3): main(), Load app/seeds/merchants_in.csv into the merchant_seed table (idempotent: clears, _sync_dsn()

### Community 61 - "App Entrypoint & Healthcheck"
Cohesion: 0.18
Nodes (6): DeclarativeBase, Account, Base, Category, Tag, Transaction

### Community 63 - "App Entry Point"
Cohesion: 0.48
Nodes (5): lensApplyCategorySelection(), lensHighlight(), lensMove(), lensRows(), lensSelectCategory()

### Community 64 - "session.py"
Cohesion: 0.23
Nodes (13): build_quickadd_preview(), _flatten_tree(), _label_for(), _default_for_dateutil(), parse_quickadd(), ParsedQuickAdd, date, Deterministic tokenizer for the Quick-Add bar (§5.1). NOT AI — pure pattern matc (+5 more)

### Community 65 - "routes.py"
Cohesion: 0.07
Nodes (28): HTTPException, get_current_user(), get_scoped_session(), Request, Verifies the Supabase JWT and extracts user_id (= auth.uid()), per §2.3 step 4., DB session for the current request: app-level scope (user.id) is layered     on, _refresh_access_token(), auth_callback() (+20 more)

### Community 66 - "main.py"
Cohesion: 0.16
Nodes (21): _accounts(), _b64(), commit(), import_page(), _parse_form_mapping(), preview(), AsyncSession, Request (+13 more)

### Community 70 - "CurrentUser"
Cohesion: 0.17
Nodes (31): CurrentUser, bulk_action(), create_txn(), delete_txn(), edit_txn_row(), _flat_categories(), get_txn_row(), list_txn_page() (+23 more)

### Community 71 - "quickadd_parser.py"
Cohesion: 0.39
Nodes (7): _call(), DB access over HTTPS (port 443) — a workaround for dev networks that firewall th, Arbitrary SQL over 443 via the Management API. Needs SUPABASE_ACCESS_TOKEN., rest_delete(), rest_insert(), rest_select(), run_sql()

### Community 72 - "importer.py"
Cohesion: 0.11
Nodes (26): analyze(), bank_signature(), chunk_bounds(), _clean_amount(), decode_bytes(), dedupe_hash(), detect_amount_convention(), detect_date_format() (+18 more)

### Community 73 - "session.py"
Cohesion: 0.29
Nodes (3): _fetch_jwks(), Verify a Supabase-issued JWT locally against the project's JWKS (ES256).     Rai, verify_access_token()

### Community 75 - "detect_series_for_merchant"
Cohesion: 0.29
Nodes (10): _amount_is_stable(), _classify_cadence(), detect_all(), detect_series_for_merchant(), DetectedSeries, date, Recurring-series detection (§4.3). The cadence/amount-stability analysis is pure, All amounts within ±tolerance of the median (subscriptions wobble a little). (+2 more)

### Community 76 - "confirm"
Cohesion: 0.23
Nodes (13): confirm(), AsyncSession, Request, recurring_page(), confirm_series(), list_series(), AsyncSession, DB-facing recurring-series operations: scan history -> upsert detected series, c (+5 more)

### Community 77 - "test_recurring.py"
Cohesion: 0.36
Nodes (10): _monthly(), date, Pure-Python recurring-detection tests — no DB (§4.3, §7 recurring behavior)., test_detect_all_skips_empty_merchant(), test_detects_monthly_subscription(), test_detects_weekly(), test_rejects_irregular_interval(), test_rejects_wild_amount_variation() (+2 more)

## Knowledge Gaps
- **87 isolated node(s):** `refresh.sh script`, `OBJC_DISABLE_INITIALIZE_FORK_SAFETY`, `GRAPHIFY_NO_BACKUP`, `Settings`, `build_css.sh script` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **53 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CurrentUser` connect `CurrentUser` to `routes.py`, `main.py`, `Database Schema & Architecture`, `Backend Service Requirements`, `UX Playbook Spec`, `confirm`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `get_account_balances()` connect `UX Playbook Spec` to `session.py`, `transactions.py`, `CurrentUser`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `safe_to_spend()` connect `transactions.py` to `UX Playbook Spec`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `get_grouped_tree()` (e.g. with `categories_page()` and `category_picker()`) actually correct?**
  _`get_grouped_tree()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `build_quickadd_preview()` (e.g. with `quickadd_commit()` and `quickadd_preview()`) actually correct?**
  _`build_quickadd_preview()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `refresh.sh script`, `OBJC_DISABLE_INITIALIZE_FORK_SAFETY`, `GRAPHIFY_NO_BACKUP` to the rest of the system?**
  _154 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Safe-to-Spend Core Concepts` be split into smaller, more focused modules?**
  _Cohesion score 0.0625 - nodes in this community are weakly interconnected._