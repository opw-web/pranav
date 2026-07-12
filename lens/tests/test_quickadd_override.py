"""Pure-Python tests for the quick-add keyword-suggestion override (§WS4b) - no DB
needed. Exercises _resolve_category_override(), the piece of the priority chain
(override > `>`/`!` forced token > auto-categorize - see build_quickadd_preview in
app/services/quickadd.py) that doesn't require a DB round trip: a tapped keyword-
suggestion chip sets category_override_id, and this is what makes that override
always win over a typed >/! token instead of the two silently disagreeing.

The rest of the flow (search_with_keywords producing the suggestion chips,
get_grouped_tree, categorize) is DB-backed raw asyncpg/SQLAlchemy `text()` SQL
against Supabase Postgres - like test_keywords.py, there is no conftest.py / DB
fixture in this repo to run that against, so most of it was verified by code
review + tracing + the WS4b report instead of an executed test. The full
priority chain *inside* build_quickadd_preview() itself, however, can be
exercised without a real DB by mocking out its four DB-backed dependencies
(get_grouped_tree, get_account_balances, categorize, search_with_keywords) -
see _run_preview() and the test_priority_chain_* tests below, same
asyncio.run()-a-coroutine style as test_add_keyword_rejects_category_not_owned_by_user
in test_keywords.py.
"""
import asyncio
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, ".")

from app.services.quickadd import _resolve_category_override, build_quickadd_preview

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


# --- Full priority chain inside build_quickadd_preview() -------------------
# override > `>`/`!` forced token > categorize(). get_grouped_tree,
# get_account_balances, categorize and search_with_keywords are the only
# DB-touching calls build_quickadd_preview makes, so mocking those four lets
# the actual if/elif priority logic run for real, unlike the unit tests above
# which only exercise _resolve_category_override() in isolation.

_TREE = [
    {"id": "cat-override", "name": "Override", "children": []},
    {"id": "cat-forced", "name": "Forced", "children": []},
]
_ACCOUNTS = [{"id": "acc-1", "name": "Checking"}]


def _run_preview(raw, category_override_id=None, categorize_result=None):
    """Runs build_quickadd_preview() with its DB-backed dependencies mocked
    out. `raw` always includes an "@checking" account token so _resolve_account
    takes the fuzzy-match-by-token branch (only calls the mocked
    get_account_balances) instead of the "no token" branch, which would need a
    real session.execute() for the last-transaction lookup."""
    categorize_mock = AsyncMock(
        return_value=categorize_result
        or {"merchant_clean": "swiggy", "category_id": "cat-auto", "confidence": "high"}
    )
    with (
        patch("app.services.quickadd.get_grouped_tree", AsyncMock(return_value=_TREE)),
        patch("app.services.quickadd.get_account_balances", AsyncMock(return_value=_ACCOUNTS)),
        patch("app.services.quickadd.categorize", categorize_mock),
        patch("app.services.quickadd.search_with_keywords", AsyncMock(return_value=([], [], None))),
    ):

        async def run():
            return await build_quickadd_preview(object(), "user-a", raw, category_override_id)

        result = asyncio.run(run())
    return result, categorize_mock


def test_priority_chain_override_wins_over_forced_token_and_categorize():
    # Chip tap (override) + a typed >token + a merchant categorize() would also
    # match - override must win, and categorize() must not even run since the
    # override short-circuits the elif chain in build_quickadd_preview().
    result, categorize_mock = _run_preview(
        "500 swiggy @checking >Forced", category_override_id="cat-override"
    )
    assert result["category_id"] == "cat-override"
    assert result["category_label"] == "Override"
    categorize_mock.assert_not_awaited()


def test_priority_chain_forced_token_wins_when_no_override():
    result, categorize_mock = _run_preview("500 swiggy @checking >Forced", category_override_id=None)
    assert result["category_id"] == "cat-forced"
    assert result["category_label"] == "Forced"
    categorize_mock.assert_not_awaited()


def test_priority_chain_falls_back_to_categorize_when_no_override_or_forced_token():
    result, categorize_mock = _run_preview("500 swiggy @checking", category_override_id=None)
    categorize_mock.assert_awaited_once()
    assert result["category_id"] == "cat-auto"
    assert result["confidence"] == "high"


def test_priority_chain_stale_override_falls_through_to_forced_token():
    # A tampered/stale override_id that doesn't resolve to one of this user's
    # own categories (see test_resolve_category_override_none_when_not_found
    # above) must fall through to the next priority level, not error or silently
    # win with a None category.
    result, categorize_mock = _run_preview(
        "500 swiggy @checking >Forced", category_override_id="someone-elses-category"
    )
    assert result["category_id"] == "cat-forced"
    categorize_mock.assert_not_awaited()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} quickadd override tests passed")
