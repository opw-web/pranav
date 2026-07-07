"""Deterministic tokenizer for the Quick-Add bar (§5.1). NOT AI — pure pattern matching.

Grammar (order-independent tokens, space-separated):
    450            -> amount (bare number)
    +50000         -> amount, and marks the transaction as income
    swiggy lunch   -> leftover words after all tokens are stripped = merchant + note
    @hdfc          -> account (fuzzy-matched against the user's account names)
    #goa           -> tag
    !food          -> force category (fuzzy match)
    >groceries     -> force category (same as !, alternate prefix)
    today / yesterday / 12 jul / 2026-07-12 -> date (defaults to today)
"""

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from dateutil import parser as dateutil_parser

_AMOUNT_RE = re.compile(r"^([+-]?)(\d+(?:\.\d+)?)$")
_ACCOUNT_RE = re.compile(r"^@(\S+)$")
_TAG_RE = re.compile(r"^#(\S+)$")
_CATEGORY_RE = re.compile(r"^[!>](\S+)$")
_DATE_WORDS = {"today", "yesterday"}


@dataclass
class ParsedQuickAdd:
    amount: float | None = None
    is_income: bool = False
    account_token: str | None = None
    tags: list[str] = field(default_factory=list)
    category_token: str | None = None
    txn_date: date = field(default_factory=date.today)
    merchant_token: str | None = None
    note: str | None = None
    raw: str = ""
    errors: list[str] = field(default_factory=list)


def parse_quickadd(raw: str, today: date | None = None) -> ParsedQuickAdd:
    today = today or date.today()
    result = ParsedQuickAdd(raw=raw, txn_date=today)
    leftover_words = []

    tokens = raw.strip().split()
    date_tokens_consumed: list[int] = []

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        m_acc = _ACCOUNT_RE.match(tok)
        if m_acc:
            result.account_token = m_acc.group(1)
            i += 1
            continue

        m_tag = _TAG_RE.match(tok)
        if m_tag:
            result.tags.append(m_tag.group(1))
            i += 1
            continue

        m_cat = _CATEGORY_RE.match(tok)
        if m_cat:
            result.category_token = m_cat.group(1)
            i += 1
            continue

        low = tok.lower()
        if low == "today":
            result.txn_date = today
            i += 1
            continue
        if low == "yesterday":
            result.txn_date = today - timedelta(days=1)
            i += 1
            continue

        # A bare number is the amount only once — a transaction has exactly one. Once
        # amount is set, a later bare number ("12" in "99 12 jul") is almost certainly
        # a date's day, so date-parsing gets first refusal on it below.
        m_amount = _AMOUNT_RE.match(tok)
        if m_amount and result.amount is None:
            sign, num = m_amount.groups()
            result.amount = float(num)
            if sign == "+":
                result.is_income = True
            i += 1
            continue

        # Try a two-token date like "12 jul"; fall back to one-token ISO/date-like strings.
        if i + 1 < len(tokens):
            two_tok = f"{tok} {tokens[i + 1]}"
            parsed = _try_parse_date(two_tok, today)
            if parsed:
                result.txn_date = parsed
                i += 2
                continue

        parsed_single = _try_parse_date(tok, today) if re.search(r"\d", tok) else None
        if parsed_single:
            result.txn_date = parsed_single
            i += 1
            continue

        leftover_words.append(tok)
        i += 1

    if leftover_words:
        result.merchant_token = leftover_words[0]
        result.note = " ".join(leftover_words[1:]) or None

    if result.amount is None:
        result.errors.append("No amount found.")

    return result


def _try_parse_date(text: str, today: date):
    try:
        parsed = dateutil_parser.parse(text, default=_default_for_dateutil(today), fuzzy=False)
        return parsed.date()
    except (ValueError, OverflowError):
        return None


def _default_for_dateutil(today: date):
    from datetime import datetime

    return datetime(today.year, today.month, today.day)
