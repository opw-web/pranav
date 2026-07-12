"""Pure-Python tests for category reason keywords (§WS4a) - no DB needed.

The rest of the feature (add_keyword/list_keywords/remove_keyword, the
categorization_rules upsert, categorize() picking the keyword rule up, and
search_with_keywords) is exercised through raw asyncpg/SQLAlchemy `text()` SQL
against Supabase Postgres, same as every other service in app/services/. Like
the rest of this test suite (test_importer.py, test_recurring.py), there is no
conftest.py / DB fixture in this repo to run that against, so those paths were
verified manually by code review + tracing (see WS4a report) rather than by an
executed test. What *is* pure and independently testable is pulled out here:
the keyword normalization rule (add_keyword) and the picker match rule
(search_with_keywords), plus the priority ordering the whole feature depends on.
"""
import sys

sys.path.insert(0, ".")

from app.services.categories import keyword_matches
from app.services.categorizer import (
    LEARNED_RULE_PRIORITY,
    USER_KEYWORD_PRIORITY,
    normalize_keyword,
)


def test_normalize_keyword_strips_and_lowercases():
    assert normalize_keyword("  Fuel  ") == "fuel"
    assert normalize_keyword("FUEL") == "fuel"


def test_normalize_keyword_empty_or_whitespace_is_empty():
    assert normalize_keyword("") == ""
    assert normalize_keyword("   ") == ""


def test_keyword_matches_prefix_and_substring_case_insensitive():
    # The example from the brief: typing "fu" should surface a "fuel" keyword.
    assert keyword_matches("fuel", "fu") is True
    assert keyword_matches("fuel", "FU") is True
    assert keyword_matches("gas station fuel", "fuel") is True  # substring, not just prefix


def test_keyword_matches_rejects_non_matching_query():
    assert keyword_matches("fuel", "food") is False


def test_keyword_matches_empty_query_never_matches():
    assert keyword_matches("fuel", "") is False
    assert keyword_matches("fuel", "   ") is False


def test_user_keyword_priority_beats_learned_rules_and_seed():
    # Explicit reason keywords must win over auto-learned merchant rules (which
    # in turn beat the shipped seed, applied at runtime with implicit priority
    # 100) - this ordering is what makes categorize() auto-apply keywords.
    assert USER_KEYWORD_PRIORITY < LEARNED_RULE_PRIORITY < 100


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print("PASS", fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} keyword tests passed")
