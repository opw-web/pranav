---
type: community
members: 12
---

# Product Idea Context

**Members:** 12 nodes

## Members
- [[AsyncSession_1]] - code
- [[CurrentUser]] - code - lens/app/auth/deps.py
- [[Default (no-query) picker view top-level groups ranked by their own +     child]] - rationale - lens/app/services/categories.py
- [[Request_4]] - code
- [[categories.py]] - code - lens/app/routers/categories.py
- [[categories_page()]] - code - lens/app/routers/categories.py
- [[category_picker()]] - code - lens/app/routers/categories.py
- [[create_category_route()]] - code - lens/app/routers/categories.py
- [[delete_category_route()]] - code - lens/app/routers/categories.py
- [[get_grouped_tree()]] - code - lens/app/services/categories.py
- [[merge_categories_route()]] - code - lens/app/routers/categories.py
- [[rename_category_route()]] - code - lens/app/routers/categories.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Product_Idea_Context
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_Backend Service Requirements]]
- 5 edges to [[_COMMUNITY_UX Playbook Spec]]
- 3 edges to [[_COMMUNITY_routes.py]]
- 1 edge to [[_COMMUNITY_main.py]]

## Top bridge nodes
- [[CurrentUser]] - degree 15, connects to 3 communities
- [[get_grouped_tree()]] - degree 10, connects to 1 community
- [[category_picker()]] - degree 6, connects to 1 community
- [[create_category_route()]] - degree 6, connects to 1 community
- [[rename_category_route()]] - degree 6, connects to 1 community