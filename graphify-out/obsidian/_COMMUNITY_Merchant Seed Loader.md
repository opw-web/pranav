---
type: community
members: 4
---

# Merchant Seed Loader

**Members:** 4 nodes

## Members
- [[Load appseedsmerchants_in.csv into the merchant_seed table (idempotent clears]] - rationale - lens/scripts/load_merchant_seed.py
- [[_sync_dsn()]] - code - lens/scripts/load_merchant_seed.py
- [[load_merchant_seed.py]] - code - lens/scripts/load_merchant_seed.py
- [[main()]] - code - lens/scripts/load_merchant_seed.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Merchant_Seed_Loader
SORT file.name ASC
```
