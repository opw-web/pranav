"""Stats page data assembly (§WS5) — category donut + monthly-trend bar. Reuses the
analytics period helpers (month_bounds, last_n_full_months) and the same SQL-first
approach as analytics.py: Python only orchestrates and computes chart geometry, no
number-crunching beyond that.

Chart geometry (donut arc dasharrays, bar x/y/height) is computed here so
templates/stats.html stays free of trig/scaling — it only loops over ready values.
Colors are handed to the template as CSS custom-property references
(`var(--series-N)`), not raw hex, so the same markup renders correctly in both
themes: stats.html defines the actual light/dark hex per slot once, following the
dataviz skill's validated categorical palette (references/palette.md).
"""

import math
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics import last_n_full_months, month_bounds

# ---- dataviz palette slots (see templates/stats.html for the actual hex per theme) ---
# Fixed hue order (blue, aqua, yellow, green, violet, red, magenta, orange) — never
# cycled or reassigned by rank change, per the dataviz skill's categorical rule.
PALETTE_SLOTS = 8
MAX_CATEGORY_SLICES = 7  # + 1 "Other" fold slot = PALETTE_SLOTS total (series-count ladder)

# ---- donut geometry --------------------------------------------------------------
_DONUT_SIZE = 200
_DONUT_CENTER = 100
_DONUT_RADIUS = 64
_DONUT_STROKE = 30
_DONUT_CIRC = 2 * math.pi * _DONUT_RADIUS
_DONUT_GAP = 3.0  # path-length gap between adjacent segments (surface-gap spacer)

# ---- bar geometry -----------------------------------------------------------------
_BAR_VB_W = 320
_BAR_VB_H = 172
_BAR_MARGIN_X = 12
_BAR_BASELINE_Y = 132
_BAR_TOP_PAD = 22
_BAR_WIDTH = 24
_BAR_MAX_HEIGHT = _BAR_BASELINE_Y - _BAR_TOP_PAD


async def category_breakdown(session: AsyncSession, user_id: str, ref: date | None = None) -> dict:
    """Current-month expense total by category, with donut arc geometry and a legend.
    Categories beyond MAX_CATEGORY_SLICES are folded into a single 'Other' slice
    (never a generated 9th hue — the dataviz skill's series-count ladder)."""
    ref = ref or date.today()
    start, end = month_bounds(ref)

    rows = (
        await session.execute(
            text(
                "SELECT COALESCE(c.name, 'Uncategorized') AS name, SUM(t.amount) AS total "
                "FROM transactions t LEFT JOIN categories c ON c.id = t.category_id "
                "WHERE t.user_id = :uid AND t.type = 'expense' AND t.is_deleted = FALSE "
                "AND t.txn_date >= :s AND t.txn_date < :e "
                "GROUP BY c.name ORDER BY total DESC"
            ),
            {"uid": user_id, "s": start, "e": end},
        )
    ).mappings().all()

    items = [{"name": r["name"], "total": float(r["total"])} for r in rows if float(r["total"]) > 0]
    total = round(sum(i["total"] for i in items), 2)

    if len(items) > MAX_CATEGORY_SLICES:
        head = items[:MAX_CATEGORY_SLICES]
        other_total = sum(i["total"] for i in items[MAX_CATEGORY_SLICES:])
        head.append({"name": "Other", "total": other_total})
        items = head

    legend = []
    for i, it in enumerate(items):
        color_var = "var(--series-other)" if it["name"] == "Other" and len(items) > MAX_CATEGORY_SLICES else f"var(--series-{i + 1})"
        pct = round((it["total"] / total * 100), 1) if total else 0.0
        legend.append({"name": it["name"], "total": round(it["total"], 2), "pct": pct, "color_var": color_var})

    segments = _donut_segments(legend, total)

    return {
        "total": total,
        "legend": legend,
        "segments": segments,
        "viewbox": f"0 0 {_DONUT_SIZE} {_DONUT_SIZE}",
        "center": _DONUT_CENTER,
        "radius": _DONUT_RADIUS,
        "stroke": _DONUT_STROKE,
    }


def _donut_segments(legend: list[dict], total: float) -> list[dict]:
    n = len(legend)
    segments = []
    cum = 0.0
    for it in legend:
        share = (it["total"] / total) if total else 0.0
        raw_len = share * _DONUT_CIRC
        gap = _DONUT_GAP if n > 1 else 0.0
        seg_len = max(raw_len - gap, 0.0)
        segments.append(
            {
                "color_var": it["color_var"],
                "name": it["name"],
                "dasharray": f"{seg_len:.2f} {max(_DONUT_CIRC - seg_len, 0):.2f}",
                "dashoffset": f"{-cum:.2f}",
            }
        )
        cum += raw_len
    return segments


def _month_starts(start: date, end: date) -> list[date]:
    """Every month-start date in [start, end)."""
    out = []
    cur = start
    while cur < end:
        out.append(cur)
        cur = date(cur.year + (1 if cur.month == 12 else 0), 1 if cur.month == 12 else cur.month + 1, 1)
    return out


async def monthly_trend(session: AsyncSession, user_id: str, ref: date | None = None, n: int = 6) -> dict:
    """Total expense spend per month for the last n full calendar months (excludes the
    current, still-in-progress month — same 'full months' semantics as category_normals).
    Returns bar geometry ready to render, plus the raw {label, total} list."""
    ref = ref or date.today()
    start, end = last_n_full_months(ref, n)

    rows = (
        await session.execute(
            text(
                "SELECT date_trunc('month', txn_date) AS m, SUM(amount) AS total FROM transactions "
                "WHERE user_id = :uid AND type = 'expense' AND is_deleted = FALSE "
                "AND txn_date >= :s AND txn_date < :e GROUP BY date_trunc('month', txn_date)"
            ),
            {"uid": user_id, "s": start, "e": end},
        )
    ).all()
    totals_by_month = {m.date() if hasattr(m, "date") else m: float(t) for m, t in rows}

    months = [
        {"month": m, "label": m.strftime("%b"), "total": round(totals_by_month.get(m, 0.0), 2)}
        for m in _month_starts(start, end)
    ]

    bars = _bar_geometry(months)
    return {"months": months, "bars": bars, "viewbox": f"0 0 {_BAR_VB_W} {_BAR_VB_H}", "baseline_y": _BAR_BASELINE_Y}


def _bar_geometry(months: list[dict]) -> list[dict]:
    n = len(months)
    if n == 0:
        return []
    max_val = max((m["total"] for m in months), default=0.0) or 1.0
    slot_w = (_BAR_VB_W - 2 * _BAR_MARGIN_X) / n
    bars = []
    for i, m in enumerate(months):
        h = round((m["total"] / max_val) * _BAR_MAX_HEIGHT, 2) if max_val else 0.0
        x = round(_BAR_MARGIN_X + i * slot_w + (slot_w - _BAR_WIDTH) / 2, 2)
        y = round(_BAR_BASELINE_Y - h, 2)
        bars.append(
            {
                "x": x,
                "y": y,
                "width": _BAR_WIDTH,
                "height": max(h, 0.0),
                "label_x": round(x + _BAR_WIDTH / 2, 2),
                "cap_y": round(y - 8, 2),
                "month_label": m["label"],
                "total": m["total"],
                "is_last": i == n - 1,
            }
        )
    return bars


async def build_stats(session: AsyncSession, user_id: str, ref: date | None = None) -> dict:
    """Assemble everything templates/stats.html needs for GET /stats."""
    ref = ref or date.today()
    donut = await category_breakdown(session, user_id, ref)
    trend = await monthly_trend(session, user_id, ref, n=6)
    return {"donut": donut, "trend": trend}
