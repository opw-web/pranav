"""Pure period-boundary math for analytics (§4.4). A wrong boundary silently corrupts
every number (the §7 Check 10 failure mode), so these are worth locking down."""
import sys
from datetime import date

sys.path.insert(0, ".")

from app.services import analytics as a


def test_month_bounds_mid_year():
    assert a.month_bounds(date(2026, 7, 15)) == (date(2026, 7, 1), date(2026, 8, 1))


def test_month_bounds_december_rolls_year():
    assert a.month_bounds(date(2026, 12, 20)) == (date(2026, 12, 1), date(2027, 1, 1))


def test_prev_month_bounds_january_rolls_back():
    assert a.prev_month_bounds(date(2026, 1, 10)) == (date(2025, 12, 1), date(2026, 1, 1))


def test_prev_month_bounds_mid_year():
    assert a.prev_month_bounds(date(2026, 7, 15)) == (date(2026, 6, 1), date(2026, 7, 1))


def test_last_3_full_months_excludes_current():
    # ref July 2026 -> last 3 full months = Apr, May, Jun => [2026-04-01, 2026-07-01)
    assert a.last_n_full_months(date(2026, 7, 15), 3) == (date(2026, 4, 1), date(2026, 7, 1))


def test_last_3_full_months_crosses_year():
    # ref Feb 2026 -> Nov 2025, Dec 2025, Jan 2026 => [2025-11-01, 2026-02-01)
    assert a.last_n_full_months(date(2026, 2, 10), 3) == (date(2025, 11, 1), date(2026, 2, 1))


def test_cur_and_prev_are_contiguous_and_non_overlapping():
    ref = date(2026, 7, 15)
    cur_start, cur_end = a.month_bounds(ref)
    prev_start, prev_end = a.prev_month_bounds(ref)
    assert prev_end == cur_start          # contiguous
    assert prev_start < prev_end <= cur_start < cur_end  # ordered, non-overlapping


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print("PASS", fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} analytics period tests passed")
