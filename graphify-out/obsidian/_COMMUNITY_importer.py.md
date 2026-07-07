---
type: community
members: 27
---

# importer.py

**Members:** 27 nodes

## Members
- [[CSV bank-statement importer (§4.2). Pure-Python detectionparsing so it is fully]] - rationale - lens/app/services/importer.py
- [[Find a strptime format that parses all sampled date strings (avoids     dateutil]] - rationale - lens/app/services/importer.py
- [[Full detection pass on an uploaded file. Returns everything the mapping wizard n]] - rationale - lens/app/services/importer.py
- [[Guess {role column_name} from header labels. Leaves out roles it can't find.]] - rationale - lens/app/services/importer.py
- [[Index of the header row. Banks often prepend account-summary junk lines,     so]] - rationale - lens/app/services/importer.py
- [[Return (start, end, has_more) for a given page — pure arithmetic, unit-testable.]] - rationale - lens/app/services/importer.py
- [[Stable hash of the normalized header row, so a bank's format is recognized next]] - rationale - lens/app/services/importer.py
- [[Turn raw CSV rows into normalized txn dicts (typeamountdatemerchant_raw).]] - rationale - lens/app/services/importer.py
- [[Within one import, flag opposite-sign same-magnitude rows on sameadjacent dates]] - rationale - lens/app/services/importer.py
- [[_clean_amount()]] - code - lens/app/services/importer.py
- [[analyze()]] - code - lens/app/services/importer.py
- [[bank_signature()]] - code - lens/app/services/importer.py
- [[chunk_bounds()]] - code - lens/app/services/importer.py
- [[date_1]] - code
- [[decode_bytes()]] - code - lens/app/services/importer.py
- [[dedupe_hash()]] - code - lens/app/services/importer.py
- [[detect_amount_convention()]] - code - lens/app/services/importer.py
- [[detect_date_format()]] - code - lens/app/services/importer.py
- [[detect_delimiter()]] - code - lens/app/services/importer.py
- [[detect_encoding()]] - code - lens/app/services/importer.py
- [[detect_header_row()]] - code - lens/app/services/importer.py
- [[extract_transactions()]] - code - lens/app/services/importer.py
- [[find_transfer_pairs()]] - code - lens/app/services/importer.py
- [[guess_mapping()]] - code - lens/app/services/importer.py
- [[importer.py]] - code - lens/app/services/importer.py
- [[parse_date()]] - code - lens/app/services/importer.py
- [[parse_rows()]] - code - lens/app/services/importer.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/importerpy
SORT file.name ASC
```
