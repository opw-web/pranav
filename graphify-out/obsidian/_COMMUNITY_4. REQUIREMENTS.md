---
type: community
members: 7
---

# 4. REQUIREMENTS

**Members:** 7 nodes

## Members
- [[4. REQUIREMENTS]] - document - LENS_V1_BUILD_PLAN.md
- [[4.1 The categorizer (servicescategorizer.py) — deterministic, learns from corrections]] - document - LENS_V1_BUILD_PLAN.md
- [[4.2 The importer (servicesimporter.py)]] - document - LENS_V1_BUILD_PLAN.md
- [[4.3 Recurring detection (servicesrecurring_detector.py)]] - document - LENS_V1_BUILD_PLAN.md
- [[4.4 Analytics (servicesanalytics.py) — all SQL-first]] - document - LENS_V1_BUILD_PLAN.md
- [[4.5 Routes (HTMX-first; most return HTML fragments, some JSON)]] - document - LENS_V1_BUILD_PLAN.md
- [[4.6 First-run onboarding (services on first login)]] - document - LENS_V1_BUILD_PLAN.md

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/4_REQUIREMENTS
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_LENS — V1 THE EXPENSE APP THAT SHOWS YOU WHY]]

## Top bridge nodes
- [[4. REQUIREMENTS]] - degree 7, connects to 1 community