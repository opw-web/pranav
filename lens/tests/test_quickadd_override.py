"""Pure-Python tests for the quick-add keyword-suggestion override (§WS4b) - no DB
needed. Exercises _resolve_category_override(), the piece of the priority chain
(override > `>`/`!` forced token > auto-categorize - see build_quickadd_preview in
app/services/quickadd.py) that doesn't require a DB round trip: a tapped keyword-
suggestion chip sets category_override_id, and this is what makes that override
always win over a typed >/! token instead of the two silently disagreeing.

The rest of the flow (search_with_keywords producing the suggestion chips,
get_grouped_tree, categorize) is DB-backed raw asyncpg/SQLAlchemy `text()` SQL
against Supabase Postgres - like test_keywords.py, there is no conftest.py / DB
fixture in this repo to run that against, so it was verified by code review +
tracing + the WS4b report instead of an executed test.
"""
import sys

sys.path.insert(0, ".")

from app.services.quickadd import _resolve_category_override

_FLAT = [
    {"id": "cat-1", "name": "Utilities", "label": "Utilities"},
    {"id": "cat-2", "name": "Fuel", "label": "Transport › Fuel"},
]


def test_resolve_category_override_matches_by_id():
    match = _resolve_category_override(_FLAT, "cat-2")
    assert match is not None
    assert match["label"] == "Transport › Fuel"


def test_resolve_category_override_none_when_blank():
    assert _resolve_category_override(_FLAT, None) is None
    assert _resolve_category_override(_FLAT, "") is None


def test_resolve_category_override_none_when_not_found():
    # Not one of this user's own categories (flat_categories is already scoped to
    # user_id via get_grouped_tree) - e.g. a stale or tampered id. Falls through to
    # the normal >token/auto-categorize resolution instead of erroring.
    assert _resolve_category_override(_FLAT, "someone-elses-category") is None


def test_resolve_category_override_none_when_no_categories():
    assert _resolve_category_override([], "cat-1") is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} quickadd override tests passed")
