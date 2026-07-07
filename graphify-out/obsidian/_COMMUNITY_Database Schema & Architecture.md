---
type: community
members: 21
---

# Database Schema & Architecture

**Members:** 21 nodes

## Members
- [[Apply a freshly-learned rule to existing uncategorized transactions whose]] - rationale - lens/app/services/categorizer.py
- [[AsyncSession_4]] - code
- [[AsyncSession_9]] - code
- [[Called when the user accepts 'Always categorize merchant as category'.]] - rationale - lens/app/routers/rules.py
- [[Create (or update) a user categorization rule from a correction (§4.1 step 4).]] - rationale - lens/app/services/categorizer.py
- [[Derive a stable 'contains' pattern from a raw merchant string, e.g.     'AMZN MK]] - rationale - lens/app/services/categorizer.py
- [[Deterministic categorizer (§4.1) — the shipped AI that is actually just rules]] - rationale - lens/app/services/categorizer.py
- [[Maps a shipped seed's 'food.restaurants' key to this user's actual category id,]] - rationale - lens/app/services/categorizer.py
- [[Request_7]] - code
- [[_learn_pattern()]] - code - lens/app/services/categorizer.py
- [[_rules_with_names()]] - code - lens/app/routers/rules.py
- [[back_apply_rule()]] - code - lens/app/services/categorizer.py
- [[categorize()]] - code - lens/app/services/categorizer.py
- [[categorizer.py]] - code - lens/app/services/categorizer.py
- [[delete_rule()]] - code - lens/app/routers/rules.py
- [[learn()]] - code - lens/app/routers/rules.py
- [[learn_rule()]] - code - lens/app/services/categorizer.py
- [[resolve_category_key()]] - code - lens/app/services/categorizer.py
- [[rules.py]] - code - lens/app/routers/rules.py
- [[rules_page()]] - code - lens/app/routers/rules.py
- [[slugify()]] - code - lens/app/services/categorizer.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Database_Schema__Architecture
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_CurrentUser]]
- 1 edge to [[_COMMUNITY_Backend Service Requirements]]
- 1 edge to [[_COMMUNITY_main.py]]
- 1 edge to [[_COMMUNITY_session.py_1]]

## Top bridge nodes
- [[categorize()]] - degree 5, connects to 2 communities
- [[learn()]] - degree 7, connects to 1 community
- [[resolve_category_key()]] - degree 6, connects to 1 community
- [[rules_page()]] - degree 5, connects to 1 community
- [[delete_rule()]] - degree 5, connects to 1 community