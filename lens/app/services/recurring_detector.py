"""Recurring-series detection (§4.3). The cadence/amount-stability analysis is pure
Python over a list of (date, amount) points, so it is fully unit-testable without a DB.
Detected series are emitted with status='detected' and NEVER auto-activated — the user
confirms them (§4.3).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median

# cadence -> (nominal interval days, matching tolerance days)
_CADENCES = {
    "weekly": (7, 2),
    "monthly": (30, 5),
    "yearly": (365, 15),
}
MIN_OCCURRENCES = 3


@dataclass
class DetectedSeries:
    merchant_clean: str
    cadence: str
    expected_amount: float
    last_seen_date: date
    next_due_date: date
    occurrences: int


def _classify_cadence(intervals: list[int]) -> str | None:
    if not intervals:
        return None
    med = median(intervals)
    for cadence, (nominal, tol) in _CADENCES.items():
        if abs(med - nominal) <= tol:
            return cadence
    return None


def _amount_is_stable(amounts: list[float], tolerance: float = 0.15) -> bool:
    """All amounts within ±tolerance of the median (subscriptions wobble a little)."""
    if not amounts:
        return False
    med = median(amounts)
    if med == 0:
        return all(a == 0 for a in amounts)
    return all(abs(a - med) / med <= tolerance for a in amounts)


def detect_series_for_merchant(
    merchant_clean: str, points: list[tuple[date, float]], amount_tolerance: float = 0.15
) -> DetectedSeries | None:
    """points = [(date, amount), ...] for one merchant. Returns a series if a regular
    interval and stable amount are found across >= MIN_OCCURRENCES."""
    if len(points) < MIN_OCCURRENCES:
        return None
    points = sorted(points, key=lambda p: p[0])
    dates = [p[0] for p in points]
    amounts = [p[1] for p in points]

    intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
    cadence = _classify_cadence(intervals)
    if cadence is None:
        return None
    if not _amount_is_stable(amounts, amount_tolerance):
        return None

    nominal = _CADENCES[cadence][0]
    last_seen = dates[-1]
    next_due = last_seen + timedelta(days=nominal)
    return DetectedSeries(
        merchant_clean=merchant_clean,
        cadence=cadence,
        expected_amount=round(median(amounts), 2),
        last_seen_date=last_seen,
        next_due_date=next_due,
        occurrences=len(points),
    )


def detect_all(grouped: dict[str, list[tuple[date, float]]]) -> list[DetectedSeries]:
    """grouped = {merchant_clean: [(date, amount), ...]}. Returns all detected series."""
    out = []
    for merchant, points in grouped.items():
        if not merchant:
            continue
        series = detect_series_for_merchant(merchant, points)
        if series:
            out.append(series)
    return out
