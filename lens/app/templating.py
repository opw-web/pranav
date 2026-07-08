"""Shared Jinja2 templates instance for every router.

Single source of truth so all pages get the same globals/filters (money,
currency_symbol, icon) instead of each router constructing its own
Jinja2Templates(). Import `templates` here instead of building a new one.
"""
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Currency ----------------------------------------------------------------

_CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
}


def currency_symbol(code: str | None) -> str:
    """Return the display symbol for a currency code, falling back to the code itself."""
    if not code:
        return _CURRENCY_SYMBOLS["INR"]
    return _CURRENCY_SYMBOLS.get(code.upper(), code.upper() + " ")


def money(value, currency: str = "INR") -> str:
    """Format a numeric amount with tabular-friendly grouping and a currency symbol.

    Example: money(1234.5) -> "₹1,234.50"
    Use with the `.money` CSS class (font-mono + tabular-nums) for alignment.
    """
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0
    symbol = currency_symbol(currency)
    return f"{symbol}{amount:,.2f}"


# --- Icons ---------------------------------------------------------------------

_SPRITE_URL = "/static/icons/sprite.svg"


def icon(name: str, css_class: str = "h-5 w-5") -> Markup:
    """Return an inline <svg><use> referencing the vendored Phosphor sprite.

    Returns Markup so Jinja renders the SVG instead of HTML-escaping it into
    visible text. Usage: {{ icon('home') }} or {{ icon('trash', 'h-4 w-4 text-accent-red-ink') }}
    """
    return Markup(
        f'<svg class="{css_class}" aria-hidden="true" focusable="false">'
        f'<use href="{_SPRITE_URL}#icon-{name}"></use></svg>'
    )


templates.env.globals["icon"] = icon
templates.env.globals["money"] = money
templates.env.globals["currency_symbol"] = currency_symbol
templates.env.filters["money"] = money
templates.env.filters["currency_symbol"] = currency_symbol
