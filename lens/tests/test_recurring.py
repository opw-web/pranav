"""Pure-Python recurring-detection tests — no DB (§4.3, §7 recurring behavior)."""
import sys
from datetime import date

sys.path.insert(0, ".")

from app.services import recurring_detector as rd


def _monthly(start: date, n: int, amount: float, jitter=0):
    pts = []
    d = start
    for i in range(n):
        amt = amount + (jitter if i % 2 else -jitter)
        pts.append((d, amt))
        # advance ~1 month
        month = d.month + 1
        year = d.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        d = date(year, month, min(d.day, 28))
    return pts


def test_detects_monthly_subscription():
    pts = _monthly(date(2026, 1, 15), 5, 199.0)
    s = rd.detect_series_for_merchant("Netflix", pts)
    assert s is not None
    assert s.cadence == "monthly"
    assert s.expected_amount == 199.0
    assert s.occurrences == 5
    # next due ~30 days after last seen
    assert (s.next_due_date - s.last_seen_date).days == 30


def test_tolerates_small_amount_wobble():
    pts = _monthly(date(2026, 1, 1), 4, 500.0, jitter=30)  # ±6% < 15%
    s = rd.detect_series_for_merchant("Gym", pts)
    assert s is not None and s.cadence == "monthly"


def test_rejects_wild_amount_variation():
    pts = [(date(2026, 1, 1), 100.0), (date(2026, 2, 1), 800.0), (date(2026, 3, 1), 250.0)]
    assert rd.detect_series_for_merchant("Groceries", pts) is None


def test_rejects_irregular_interval():
    pts = [(date(2026, 1, 1), 100.0), (date(2026, 1, 8), 100.0), (date(2026, 3, 20), 100.0)]
    assert rd.detect_series_for_merchant("Random", pts) is None


def test_requires_min_occurrences():
    pts = [(date(2026, 1, 1), 100.0), (date(2026, 2, 1), 100.0)]
    assert rd.detect_series_for_merchant("TwoOnly", pts) is None


def test_detects_weekly():
    pts = [(date(2026, 1, 1), 50.0), (date(2026, 1, 8), 50.0), (date(2026, 1, 15), 50.0), (date(2026, 1, 22), 50.0)]
    s = rd.detect_series_for_merchant("Weekly Cleaner", pts)
    assert s is not None and s.cadence == "weekly"


def test_detect_all_skips_empty_merchant():
    grouped = {"": _monthly(date(2026, 1, 1), 4, 100.0), "Spotify": _monthly(date(2026, 1, 1), 4, 119.0)}
    out = rd.detect_all(grouped)
    assert len(out) == 1 and out[0].merchant_clean == "Spotify"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print("PASS", fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} recurring tests passed")
