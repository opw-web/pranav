---
type: community
members: 24
---

# Backend Service Requirements

**Members:** 24 nodes

## Members
- [[AsyncSession_1]] - code
- [[AsyncSession_8]] - code
- [[Category tree, fuzzy picker search, and createrenamemerge — reused by the mana]] - rationale - lens/app/services/categories.py
- [[Default (no-query) picker view top-level groups ranked by their own +     child]] - rationale - lens/app/services/categories.py
- [[Flat, ranked results across the whole tree for a non-empty query (§5.2).]] - rationale - lens/app/services/categories.py
- [[MaxDepthError]] - code - lens/app/services/categories.py
- [[Reassign all of source's transactions (and children) to target, then delete sour]] - rationale - lens/app/services/categories.py
- [[Request_4]] - code
- [[ValueError]] - code
- [[_all_categories_with_usage()]] - code - lens/app/services/categories.py
- [[categories.py]] - code - lens/app/routers/categories.py
- [[categories.py_1]] - code - lens/app/services/categories.py
- [[categories_page()]] - code - lens/app/routers/categories.py
- [[category_picker()]] - code - lens/app/routers/categories.py
- [[create_category()]] - code - lens/app/services/categories.py
- [[create_category_route()]] - code - lens/app/routers/categories.py
- [[delete_category()]] - code - lens/app/services/categories.py
- [[delete_category_route()]] - code - lens/app/routers/categories.py
- [[fuzzy_search()]] - code - lens/app/services/categories.py
- [[get_grouped_tree()]] - code - lens/app/services/categories.py
- [[merge_categories()]] - code - lens/app/services/categories.py
- [[merge_categories_route()]] - code - lens/app/routers/categories.py
- [[rename_category()]] - code - lens/app/services/categories.py
- [[rename_category_route()]] - code - lens/app/routers/categories.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Backend_Service_Requirements
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_CurrentUser]]
- 1 edge to [[_COMMUNITY_Database Schema & Architecture]]
- 1 edge to [[_COMMUNITY_session.py_1]]

## Top bridge nodes
- [[get_grouped_tree()]] - degree 13, connects to 3 communities
- [[category_picker()]] - degree 6, connects to 1 community
- [[create_category_route()]] - degree 6, connects to 1 community
- [[rename_category_route()]] - degree 6, connects to 1 community
- [[merge_categories_route()]] - degree 6, connects to 1 community