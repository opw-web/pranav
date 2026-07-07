---
type: community
members: 9
---

# 2. ARCHITECTURE

**Members:** 9 nodes

## Members
- [[2. ARCHITECTURE]] - document - LENS_V1_BUILD_PLAN.md
- [[2.1 Tech stack (install these exactly)]] - document - LENS_V1_BUILD_PLAN.md
- [[2.2 Accounts & keys you need]] - document - LENS_V1_BUILD_PLAN.md
- [[2.3 Auth flow (Google via Supabase)]] - document - LENS_V1_BUILD_PLAN.md
- [[2.4 Folder structure (create this now)]] - document - LENS_V1_BUILD_PLAN.md
- [[2.5 Database schema (run this SQL; adjust types as you like)]] - document - LENS_V1_BUILD_PLAN.md
- [[2.5.1 RLS policies (MANDATORY — do not skip)]] - document - LENS_V1_BUILD_PLAN.md
- [[2.6 The SQL-first analytics rule (why no pandas)]] - document - LENS_V1_BUILD_PLAN.md
- [[2.7 Deployment notes (Vercel + serverless reality)]] - document - LENS_V1_BUILD_PLAN.md

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/2_ARCHITECTURE
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_LENS — V1 THE EXPENSE APP THAT SHOWS YOU WHY]]

## Top bridge nodes
- [[2. ARCHITECTURE]] - degree 8, connects to 1 community