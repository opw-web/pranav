"""CSV bank-statement importer (§4.2). Pure-Python detection/parsing so it is fully
testable without a DB; the DB-touching parts (dedupe lookup, commit) take a session.

Pipeline: detect -> map -> preview(dedupe + transfer flags) -> chunked commit.
"""

import csv
import hashlib
import io
import re
from datetime import date, datetime

from charset_normalizer import from_bytes
from dateutil import parser as dateparser

# Column-role guessing: header keyword -> role. Order matters — debit/credit are
# checked before the generic `amount` so specific columns like "Withdrawal Amt" are
# claimed as debit rather than swallowed by the greedy "amt" hint.
_HEADER_HINTS = {
    "date": ["date", "txn date", "transaction date", "value date", "posting date", "tran date"],
    "debit": ["withdrawal amt", "withdrawal", "debit amount", "debit", "paid out", "dr"],
    "credit": ["deposit amt", "deposit", "credit amount", "credit", "paid in", "cr"],
    "amount": ["transaction amount", "amount", "amt"],
    "desc": ["description", "narration", "particulars", "details", "remarks", "transaction remarks", "narrative"],
    "balance": ["closing balance", "running balance", "available balance", "balance"],
    "ref": ["reference number", "reference", "ref no", "ref", "cheque", "chq"],
}

_COMMON_DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%y", "%d-%m-%y",
    "%d %b %Y", "%d-%b-%Y", "%d-%b-%y", "%d %B %Y", "%Y/%m/%d", "%m-%d-%Y",
]


def detect_encoding(raw: bytes) -> str:
    best = from_bytes(raw).best()
    return best.encoding if best else "utf-8"


def decode_bytes(raw: bytes) -> str:
    return raw.decode(detect_encoding(raw), errors="replace")


def detect_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        # fall back to whichever candidate appears most in the first line
        first = sample.splitlines()[0] if sample.splitlines() else sample
        return max(",;\t|", key=lambda d: first.count(d))


def detect_header_row(rows: list[list[str]]) -> int:
    """Index of the header row. Banks often prepend account-summary junk lines,
    so we pick the first row whose cells look like column labels (mostly non-numeric,
    matching known header keywords) and that has the most columns."""
    best_idx, best_score = 0, -1
    all_hints = [h for hints in _HEADER_HINTS.values() for h in hints]
    for i, row in enumerate(rows[:15]):
        non_empty = [c for c in row if c.strip()]
        if len(non_empty) < 2:
            continue
        keyword_hits = sum(
            1 for c in non_empty if any(h in c.strip().lower() for h in all_hints)
        )
        numeric = sum(1 for c in non_empty if re.fullmatch(r"[-+]?[\d,.\s]+", c.strip()))
        score = keyword_hits * 10 + len(non_empty) - numeric * 3
        if score > best_score:
            best_idx, best_score = i, score
    return best_idx


def guess_mapping(header: list[str]) -> dict:
    """Guess {role: column_name} from header labels. Leaves out roles it can't find."""
    mapping = {}
    used = set()
    for role, hints in _HEADER_HINTS.items():
        for col in header:
            if col in used:
                continue
            label = col.strip().lower()
            if any(label == h or h in label for h in hints):
                mapping[role] = col
                used.add(col)
                break
    return mapping


def detect_amount_convention(mapping: dict) -> str:
    if "debit" in mapping or "credit" in mapping:
        return "debit_credit_columns"
    return "signed"


def _clean_amount(s: str) -> float | None:
    if s is None:
        return None
    s = s.strip().replace(",", "").replace("₹", "").replace("INR", "").strip()
    if s in ("", "-"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if not m:
        return None
    val = float(m.group())
    return -val if neg else val


def detect_date_format(samples: list[str]) -> str | None:
    """Find a strptime format that parses all sampled date strings (avoids
    dateutil's ambiguous day/month guessing when a consistent format exists)."""
    samples = [s for s in samples if s and s.strip()][:20]
    if not samples:
        return None
    for fmt in _COMMON_DATE_FORMATS:
        try:
            for s in samples:
                datetime.strptime(s.strip(), fmt)
            return fmt
        except ValueError:
            continue
    return None


def parse_date(value: str, date_format: str | None) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    if date_format:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            pass
    try:
        return dateparser.parse(value, dayfirst=True).date()
    except (ValueError, OverflowError, TypeError):
        return None


def bank_signature(header: list[str]) -> str:
    """Stable hash of the normalized header row, so a bank's format is recognized next time."""
    norm = "|".join(sorted(c.strip().lower() for c in header if c.strip()))
    return hashlib.sha256(norm.encode()).hexdigest()[:32]


def dedupe_hash(account_id: str, txn_date: date, amount: float, merchant_raw: str) -> str:
    key = f"{account_id}|{txn_date.isoformat()}|{amount:.2f}|{(merchant_raw or '').strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()


def parse_rows(text: str, delimiter: str, header_idx: int) -> tuple[list[str], list[list[str]]]:
    reader = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    reader = [r for r in reader if any(c.strip() for c in r)]  # drop blank lines
    if not reader:
        return [], []
    header = [c.strip() for c in reader[header_idx]]
    data = reader[header_idx + 1:]
    return header, data


def analyze(raw: bytes) -> dict:
    """Full detection pass on an uploaded file. Returns everything the mapping wizard needs."""
    text = decode_bytes(raw)
    delimiter = detect_delimiter(text[:4096])
    all_rows = [r for r in csv.reader(io.StringIO(text), delimiter=delimiter) if any(c.strip() for c in r)]
    header_idx = detect_header_row(all_rows)
    header, data = parse_rows(text, delimiter, header_idx)
    mapping = guess_mapping(header)
    convention = detect_amount_convention(mapping)

    date_fmt = None
    if "date" in mapping:
        col_idx = header.index(mapping["date"])
        samples = [r[col_idx] for r in data[:20] if len(r) > col_idx]
        date_fmt = detect_date_format(samples)

    return {
        "delimiter": delimiter,
        "header": header,
        "header_idx": header_idx,
        "mapping": mapping,
        "amount_convention": convention,
        "date_format": date_fmt,
        "signature": bank_signature(header),
        "preview_rows": data[:5],
        "total_rows": len(data),
    }


def extract_transactions(
    header: list[str], data: list[list[str]], mapping: dict, date_format: str | None, amount_convention: str
) -> list[dict]:
    """Turn raw CSV rows into normalized txn dicts (type/amount/date/merchant_raw).
    Amount sign: signed column -> negative = expense; debit/credit columns -> debit = expense."""
    def idx(role):
        col = mapping.get(role)
        return header.index(col) if col and col in header else None

    di, ai, dbi, ci, desci = idx("date"), idx("amount"), idx("debit"), idx("credit"), idx("desc")
    out = []
    for row in data:
        def cell(i):
            return row[i] if i is not None and i < len(row) else ""

        txn_date = parse_date(cell(di), date_format)
        if txn_date is None:
            continue

        if amount_convention == "debit_credit_columns":
            debit = _clean_amount(cell(dbi))
            credit = _clean_amount(cell(ci))
            if debit:
                txn_type, amount = "expense", abs(debit)
            elif credit:
                txn_type, amount = "income", abs(credit)
            else:
                continue
        else:
            signed = _clean_amount(cell(ai))
            if signed is None:
                continue
            txn_type = "income" if signed > 0 else "expense"
            amount = abs(signed)

        if amount == 0:
            continue

        out.append({
            "txn_date": txn_date,
            "type": txn_type,
            "amount": round(amount, 2),
            "merchant_raw": cell(desci).strip() or None,
        })
    return out


CHUNK_SIZE = 200  # rows committed per request, to stay well under serverless time limits (§2.7)


def chunk_bounds(total: int, page: int, size: int = CHUNK_SIZE) -> tuple[int, int, bool]:
    """Return (start, end, has_more) for a given page — pure arithmetic, unit-testable."""
    start = page * size
    end = min(start + size, total)
    return start, end, end < total


def find_transfer_pairs(txns: list[dict], day_tolerance: int = 1) -> list[tuple[int, int]]:
    """Within one import, flag opposite-sign same-magnitude rows on same/adjacent dates
    as candidate transfers (§4.2). Returns index pairs (expense_idx, income_idx)."""
    pairs = []
    used = set()
    for i, a in enumerate(txns):
        if i in used or a["type"] != "expense":
            continue
        for j, b in enumerate(txns):
            if j in used or j == i or b["type"] != "income":
                continue
            if abs(a["amount"] - b["amount"]) < 0.01 and abs((a["txn_date"] - b["txn_date"]).days) <= day_tolerance:
                pairs.append((i, j))
                used.add(i)
                used.add(j)
                break
    return pairs
