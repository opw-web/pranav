"""Pure savings math (§WS6). Locks down the recommendation formula without a DB."""
import sys

sys.path.insert(0, ".")

from app.routers.settings import _parse_optional_amount
from app.services import savings as s


def test_compute_recommended_basic():
    r = s.compute_recommended(100_000, 35_000, 40_000)
    assert r["recommended"] == 25_000
    assert r["has_income"] is True
    assert "₹25,000" in r["guidance"]


def test_compute_recommended_overspend():
    r = s.compute_recommended(50_000, 30_000, 30_000)
    assert r["recommended"] == -10_000
    assert "exceeds your income" in r["guidance"]


def test_compute_recommended_no_history():
    r = s.compute_recommended(80_000, 0, 0)
    assert r["recommended"] == 80_000
    assert "add a few transactions" in r["guidance"]


def test_compute_recommended_goal_met():
    r = s.compute_recommended(100_000, 35_000, 40_000, savings_goal=20_000)
    assert "covers your ₹20,000 savings goal" in r["guidance"]


def test_compute_recommended_goal_above_recommended():
    r = s.compute_recommended(100_000, 35_000, 40_000, savings_goal=30_000)
    assert "₹5,000 above" in r["guidance"]


def test_parse_optional_amount_empty_is_none():
    assert _parse_optional_amount("") is None
    assert _parse_optional_amount("   ") is None
    assert _parse_optional_amount(None) is None


def test_parse_optional_amount_valid():
    assert _parse_optional_amount("1500") == 1500.0
    assert _parse_optional_amount("  2500.50 ") == 2500.50


def test_parse_optional_amount_garbage_does_not_raise():
    # Non-numeric POST body must never 500 the request — treat as "no value".
    assert _parse_optional_amount("abc") is None
    assert _parse_optional_amount("12,000") is None


def test_parse_optional_amount_negative_rejected():
    assert _parse_optional_amount("-500") is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} savings tests passed")
