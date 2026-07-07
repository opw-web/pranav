---
type: community
members: 8
---

# test_importer.py

**Members:** 8 nodes

## Members
- [[Pure-Python importer tests — no DB needed. Covers §4.2 detection + §7 Checks 67]] - rationale - lens/tests/test_importer.py
- [[test_amount_cleaning()]] - code - lens/tests/test_importer.py
- [[test_bank_signature_stable_and_distinct()]] - code - lens/tests/test_importer.py
- [[test_dedupe_hash_identical_rows()]] - code - lens/tests/test_importer.py
- [[test_hdfc_debit_credit_detection()]] - code - lens/tests/test_importer.py
- [[test_icici_signed_semicolon()]] - code - lens/tests/test_importer.py
- [[test_importer.py]] - code - lens/tests/test_importer.py
- [[test_transfer_pair_detection()]] - code - lens/tests/test_importer.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_importerpy
SORT file.name ASC
```
