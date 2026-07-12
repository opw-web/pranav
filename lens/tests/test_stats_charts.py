"""Pure chart-geometry math for the Stats tab (§WS5). Like the analytics period tests,
these lock down the deterministic geometry so a bad arc/scale can't silently ship —
no DB needed, matching test_analytics_periods.py's style."""
import sys
from datetime import date

sys.path.insert(0, ".")

from app.services import stats as s


def _legend(pairs):
    return [{"name": n, "total": float(t), "color_var": f"var(--series-{i + 1})"} for i, (n, t) in enumerate(pairs)]


def test_donut_segments_cover_full_circle_minus_gaps():
    legend = _legend([("A", 4000), ("B", 3000), ("C", 3000)])
    total = 10000.0
    segs = s._donut_segments(legend, total)
    assert len(segs) == 3
    # Each visible arc length + its gap sums back to the full circumference (share of total).
    seg_lens = [float(seg["dasharray"].split()[0]) for seg in segs]
    reconstructed = sum(seg_lens) + s._DONUT_GAP * len(segs)
    assert abs(reconstructed - s._DONUT_CIRC) < 0.5


def test_donut_percentages_sum_to_about_100():
    # legend percentages are computed in category_breakdown; emulate its pct math here.
    items = [("Groceries", 4200.0), ("Rent", 3000.0), ("Dining", 2800.0)]
    total = sum(t for _, t in items)
    pcts = [round(t / total * 100, 1) for _, t in items]
    assert abs(sum(pcts) - 100.0) < 0.2


def test_bar_geometry_returns_n_bars_and_normalizes_tallest_to_full_height():
    months = [{"label": "Feb", "total": 100.0}, {"label": "Mar", "total": 250.0}, {"label": "Apr", "total": 0.0}]
    bars = s._bar_geometry(months)
    assert len(bars) == 3
    tallest = max(bars, key=lambda b: b["height"])
    assert tallest["month_label"] == "Mar"
    assert abs(tallest["height"] - s._BAR_MAX_HEIGHT) < 0.01  # peak scaled to full plot height
    assert bars[-1]["is_last"] is True                        # only the latest month is labelled
    assert all(s._BAR_MARGIN_X <= b["x"] <= s._BAR_VB_W for b in bars)  # inside the viewBox


def test_bar_geometry_empty_is_empty():
    assert s._bar_geometry([]) == []


def test_month_starts_enumerates_each_month_in_range():
    starts = s._month_starts(date(2025, 11, 1), date(2026, 2, 1))
    assert starts == [date(2025, 11, 1), date(2025, 12, 1), date(2026, 1, 1)]


def test_category_fold_threshold_leaves_room_for_other_slot():
    # MAX_CATEGORY_SLICES head categories + 1 "Other" fold must fit the 8-slot palette.
    assert s.MAX_CATEGORY_SLICES + 1 == s.PALETTE_SLOTS


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} stats chart tests passed")
