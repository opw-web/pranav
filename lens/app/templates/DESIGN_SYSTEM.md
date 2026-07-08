# LENS Design System — "Soft Structuralism" (soft-premium)

This is the contract for every page-builder agent. Foundation lives in:

- `lens/app/static/css/input.css` — Tailwind v4 CSS-first tokens + components
  → compiles to `lens/app/static/css/app.css` (run `bash lens/scripts/build_css.sh` after any edit)
- `lens/app/templates/base.html` — shell (nav, quick-add, tab bar, sheets, toast region)
- `lens/app/static/js/app.js` — shell/interaction JS (keyboard map, sheets, theme, reveal)
- `lens/app/templating.py` — shared `templates` (Jinja2Templates) with `money`, `currency_symbol`, `icon` globals/filters
- `lens/app/static/icons/sprite.svg` — vendored Phosphor icon symbols
- `lens/app/static/fonts/` — vendored Geist + Geist Mono (woff2, OFL license)

**Do not edit base.html, input.css, app.js, templating.py, or the sprite** from
a page-builder agent — this is the shared foundation. Screens should only use
the tokens/classes documented below via Tailwind utilities + component classes.

Direction: warm, high-end-agency depth. Tinted soft shadows (never pure
black), tactile double-bezel surfaces, one calm confident accent color, pastel
semantic pairs, refined micro-motion. No purple. No neon. No CDN.

---

## 1. Color tokens

Every token is a Tailwind color (`bg-*`, `text-*`, `border-*`).

| Utility base | Light | Dark | Use |
|---|---|---|---|
| `canvas` | `#FBFAF8` | `#17150F` | page background (already on `<body>`) |
| `surface` | `#FFFFFF` | `#201D18` | cards, bars, sheets |
| `ink` | `#191817` | `#F4F1EA` | primary text |
| `ink-soft` | `#55514B` | `#C9C3B8` | headings / secondary-strong text |
| `muted` | `#8A857D` | `#948D80` | secondary / helper text |
| `hair` | `rgba(25,22,20,.07)` | `rgba(244,241,234,.08)` | default hairline: `border-hair` |
| `hair-strong` | `rgba(25,22,20,.12)` | `rgba(244,241,234,.16)` | opaque-feeling hairline (inputs) |
| `brand` / `brand-ink` | `#1E7A56` / `#FFFFFF` | same | primary actions, active states |
| `brand-soft` | `#E8F2EC` | tinted dark green | focus rings, selection, hover fills |

Dark mode is driven by **both** `@media (prefers-color-scheme: dark)` and
`:root[data-theme="dark"|"light"]` — the explicit attribute (written by the
theme toggle in the More sheet, see §7) always wins over OS preference in
either direction. Don't hand-roll dark variants; the tokens already flip.

### Semantic accent PAIRS (background + `-ink` text) — always pair them

| State | bg utility | text utility |
|---|---|---|
| safe / positive | `bg-accent-green` | `text-accent-green-ink` |
| spike / over / negative | `bg-accent-red` | `text-accent-red-ink` |
| upcoming / warn | `bg-accent-amber` | `text-accent-amber-ink` |
| info | `bg-accent-blue` | `text-accent-blue-ink` |

```html
<span class="chip bg-accent-green text-accent-green-ink">Income</span>
```

### Fonts

| Utility | Stack | Use |
|---|---|---|
| `font-sans` | Geist (vendored) → system-ui, "SF Pro Display", "Segoe UI", sans-serif | default UI (already on body) |
| `font-mono` | Geist Mono (vendored) → ui-monospace, SF Mono, Menlo | **use via the `.money` class**, codes, `.kbd` |

Fonts are self-hosted woff2 in `app/static/fonts/` with `font-display: swap`,
so there is no CDN dependency and no flash-of-invisible-text beyond the swap.

### Radii & shadows

`rounded-control` (12px: buttons/inputs/chips) · `rounded-card` (20px: cards)
· `rounded-sheet` (28px: sheet top corners). `rounded-full` for pills/dots.

`shadow-card` (default card lift) · `shadow-pop` (nav islands, sheets,
popovers) · `shadow-inset` (used internally by `.core`, the double-bezel
inner surface). All shadows are soft and warm-tinted — never pure black.
Don't invent new shadow values.

---

## 2. Double-bezel surfaces (`.shell` / `.core`)

The signature "tactile" premium container: an outer recessed frame (`.shell`)
around an inner lit surface (`.core`). Used for the quick-add island and the
desktop top nav; reuse it for any hero/premium card on a page.

```html
<div class="shell">
  <div class="core p-5">
    <p class="eyebrow mb-2">Safe to spend</p>
    <p class="money text-4xl text-ink">₹12,480.00</p>
  </div>
</div>
```

`.shell` = padding-4px frame with `bg-hair` + `shadow-card`, `border-radius`
4px larger than `--radius-card`. `.core` = the actual surface: `bg-surface`,
`border`, `shadow-inset`, `border-radius: var(--radius-card)`.

---

## 3. Buttons (button-in-button ready)

```html
<button class="btn btn-primary">Save</button>
<button class="btn btn-secondary">Cancel</button>
<button class="btn btn-ghost">Skip</button>
```

All variants are 44px min-height, and `:active` scales to `.98` for tactile
feedback (respects `prefers-reduced-motion`). Nesting a smaller `.btn` inside
a `.core`/`.card` surface ("button in button") is a supported pattern — no
extra classes needed, e.g. the island-nav's `Add` button sits inside the nav
pill. Style links as buttons by adding the same classes to `<a>`.

---

## 4. Money & icons

### `.money` class + Jinja `money()` filter/global

```html
<p class="money text-2xl {{ 'text-accent-red-ink' if t.type=='expense' else 'text-accent-green-ink' }}">
  {{ money(t.amount, t.currency) }}
</p>
```

`money(value, currency='INR')` → tabular-formatted string with symbol, e.g.
`money(1234.5)` → `"₹1,234.50"`. Also available as a filter: `{{ amount|money }}`.
`currency_symbol(code)` returns just the symbol/prefix. The `.money` CSS
class applies `font-mono` + `font-variant-numeric: tabular-nums` — always put
it on the element wrapping a formatted amount even if you format the number
yourself.

### `icon()` global — inline SVG from the vendored Phosphor sprite

```html
{{ icon('home') }}                          <!-- default h-5 w-5 -->
{{ icon('trash', 'h-4 w-4 text-accent-red-ink') }}
```

Available names (see `app/static/icons/sprite.svg`): `home`, `receipt`,
`chart`, `repeat`, `wallet`, `plus`, `search`, `pencil`, `trash`, `tag`,
`check`, `x`, `arrow-up-right`, `caret-down`, `upload`, `gear`, `sparkle`,
`warning`, `arrow-counter-clockwise`. Need another? Add a `<symbol>` to the
sprite (foundation-owned file) rather than inlining ad-hoc SVGs in a page.

---

## 5. Layout rules

- Content wrapper: `mx-auto max-w-6xl w-full px-3 md:px-6`. `base.html`
  already wraps `{% block content %}` inside `<main>` — screens just emit
  content.
- Vertical rhythm inside a screen: `space-y-4` / `space-y-5`.
- Tap targets ≥ 44px (component classes enforce this already).
- The mobile tab bar floats above content; `<main>` already has `pb-32`
  clearance. Don't add your own bottom-fixed bars on mobile.
- Set the active nav item from the router via `active_tab` in the context
  (`"home"` / `"txn"` / `"insights"` / `"recurring"` / `"accounts"`).
  Optional. Set the mobile top-bar contextual title with
  `{% block topbar_title %}Transactions{% endblock %}`.

### Responsive tables — required pattern

Mobile shows **list-cards** (`.list-row`); desktop (`md:+`) shows a
**table**. Render both, toggle with utilities. Keep `#txn-tbody` and
`tr[id^='txn-row-']` intact — the global keyboard row-nav depends on it.

```html
<div class="md:hidden shell"><div class="core divide-y divide-hair">
  {% for t in items %}{# .list-row markup #}{% endfor %}
</div></div>

<div class="hidden md:block card overflow-x-auto">
  <table class="w-full text-sm">
    <tbody id="txn-tbody">{# existing txn_row.html rows #}</tbody>
  </table>
</div>
```

---

## 6. Patterns (copy-paste)

### Card
```html
<div class="card p-5">
  <p class="text-sm font-medium text-ink">Title</p>
  <p class="text-sm text-muted mt-1">Body…</p>
</div>
```

### Eyebrow (tiny uppercase tracking label)
```html
<p class="eyebrow">Safe to spend</p>
```

### Chip / category chip (user color preserved — do NOT theme-ify)
```html
<span class="chip" style="background: {{ color }}22; color: {{ color }}">{{ name }}</span>
<span class="chip bg-hair text-muted">Uncategorized</span>
```

### Pill (standalone floating badge, distinct from `.chip`)
```html
<span class="pill">{{ icon('sparkle', 'h-3.5 w-3.5') }} New</span>
```

### List row (amount + category chip)
```html
<a class="list-row" hx-get="/txn/{{ t.id }}/edit" hx-target="…" hx-swap="outerHTML">
  <div class="min-w-0 flex-1">
    <p class="text-sm text-ink truncate">{{ t.merchant_clean or '—' }}</p>
    <p class="text-xs text-muted truncate">{{ t.txn_date }} · {{ t.account_name }}</p>
  </div>
  {% if t.category_name %}
  <span class="chip" style="background: {{ t.category_color }}22; color: {{ t.category_color }}">{{ t.category_name }}</span>
  {% endif %}
  <span class="money text-sm whitespace-nowrap
    {{ 'text-accent-red-ink' if t.type == 'expense' else ('text-accent-green-ink' if t.type in ('income','refund') else 'text-muted') }}">
    {{ '-' if t.type == 'expense' else ('+' if t.type in ('income','refund') else '') }}{{ money(t.amount, t.currency) }}
  </span>
</a>
```

### Form field
```html
<label class="field-label">Amount</label>
<input name="amount" class="field" />
<!-- error variant -->
<input class="field border-accent-red-ink" aria-invalid="true" />
```

### Segmented control
```html
<div class="segment" role="tablist">
  <button class="segment-item is-active" aria-selected="true">Month</button>
  <button class="segment-item">Week</button>
  <button class="segment-item">Year</button>
</div>
```

### Bottom sheet (mobile dialog; centers at md:+)
```html
<button onclick="lensOpenSheet('my-sheet')" class="btn btn-secondary">Open</button>

<div id="my-sheet" x-cloak class="sheet-backdrop hidden"
     onclick="if(event.target===this) lensCloseSheet('my-sheet')">
  <div class="sheet" role="dialog" aria-label="Title">
    <div class="sheet-grabber"></div>
    <!-- content -->
    <button onclick="lensCloseSheet('my-sheet')" class="btn btn-primary w-full mt-3">Done</button>
  </div>
</div>
```
JS helpers: `lensOpenSheet(id)` / `lensCloseSheet(id)` (in app.js).

### Skeleton (shimmer)
```html
<div class="space-y-2">
  <div class="skeleton h-4 w-2/3"></div>
  <div class="skeleton h-4 w-1/2"></div>
</div>
```

### Keyboard key badge
```html
Press <span class="kbd">a</span> to focus quick-add.
```

### Scroll-reveal
```html
<div class="reveal">Fades + slides up once scrolled into view.</div>
```
Wired by an `IntersectionObserver` in `app.js` (adds `.is-visible`); re-scans
after `htmx:afterSwap` so content swapped in by HTMX gets observed too.
Fully neutralized under `prefers-reduced-motion: reduce`.

### Empty state
```html
<div class="text-center py-16 max-w-sm mx-auto">
  <p class="text-xl font-semibold text-ink mb-1">No transactions yet</p>
  <p class="text-sm text-muted mb-6">Add your first one to get started.</p>
  <button onclick="lensToggleQuickadd()" class="btn btn-primary">Quick add</button>
</div>
```

### Error state (inline)
```html
<div class="rounded-control bg-accent-red text-accent-red-ink text-sm px-3 py-2">
  Couldn't save — check the amount and try again.
</div>
```

### Wizard steps (import wizard etc.)
```html
<div data-wiz-step="1">Step 1…</div>
<div data-wiz-step="2" class="hidden">Step 2…</div>
<button onclick="lensWizStep(2)" class="btn btn-primary">Next</button>
<!-- optional progress dots -->
<span data-wiz-dot="1" class="segment-item is-active"></span>
<span data-wiz-dot="2" class="segment-item"></span>
```
`lensWizStep(n)` shows the `[data-wiz-step="n"]` element and hides siblings;
toggles `.is-active` on matching `[data-wiz-dot="n"]` elements.

---

## 7. Theme (light / dark / system)

Toggle lives in the mobile "More" sheet (`base.html`), a `.segment` of
Light / Dark / Auto buttons calling `lensSetTheme('light'|'dark'|'system')`.
It writes `data-theme` on `<html>` + `localStorage['lens-theme']`; an inline
`<script>` in `<head>` applies the saved value before first paint (no flash).
Pages never need to touch this — just use the color tokens and both modes
follow automatically.

---

## 8. Motion rules

- Standard eases: `--ease-soft` (`cubic-bezier(.22,1,.36,1)`) for
  fades/reveals, `--ease-snap` (`cubic-bezier(.16,1,.3,1)`) for sheets/pop-ins
  and button `:active` scale. Don't invent new curves.
- `@media (prefers-reduced-motion: reduce)` neutralizes all animations and
  transitions globally (already in `input.css`) — no per-component opt-out
  needed.
- Sheets animate in (`lens-slide-up` mobile / `lens-pop-in` desktop),
  skeletons shimmer, reveals fade+slide. Don't add additional page-level
  transitions beyond `.reveal` and the component defaults.

---

## 9. Do / Don't

- DO use accent pairs together; DON'T mix a pale bg with an unrelated ink color.
- DO wrap amounts in `.money` (or use the `money()` filter which callers still wrap in `.money`); DON'T use plain `font-mono` for amounts without `tabular-nums`.
- DON'T introduce new hex colors, shadows, or easing curves — use tokens.
- DON'T add CDN assets, Google Fonts links, or additional web fonts.
- DON'T rename/remove any contract id or JS helper name in §10.

---

## 10. Preserved contract (do not rename/remove)

### DOM ids / selectors (base.html)
`#quickadd-shell`, `#quickadd-bar` (`<input name="raw">`, `hx-post="/txn/quickadd/preview"`,
`hx-trigger="keyup changed delay:150ms"`, `hx-target="#quickadd-preview"`),
wrapping `<form hx-post="/txn/quickadd" hx-target="#quickadd-result">`,
`#quickadd-preview`, `#quickadd-result`, `#learn-offer-region`,
`#toast-region`, `#more-sheet`, `#lens-cheatsheet`. Body attribute
`hx-headers='{"X-Requested-With":"htmx"}'` on `<body>`. Transaction table
contract: `#txn-tbody` + `tr[id^='txn-row-']` (owned by transactions.html /
partials, but keyboard nav in app.js depends on the ids existing).

### Jinja blocks / vars
`{% block title %}`, `{% block topbar_title %}`, `{% block content %}`,
`active_tab` (`"home"|"txn"|"insights"|"recurring"|"accounts"`).

### app.js public names (unchanged signatures)
`lensToggleQuickadd()`, `lensOpenSheet(id)`, `lensCloseSheet(id)`,
`lensWizStep(n)`, `window.lensCategoryTarget`,
`lensApplyCategorySelection(id, name)`, `lensSelectCategory(el)`.

### Keyboard map (global keydown listener)
`a` focus quick-add · `/` search · `j`/`k` row nav over
`#txn-tbody tr[id^='txn-row-']` (ring highlight + `scrollIntoView`) · `e` edit
(`htmx.ajax GET /txn/{id}/edit`) · `c` set-category · `t` tag · `x`
toggle-select checkbox · `u` undo (clicks latest toast's Undo button) · `?`
cheatsheet · `Esc` blur/close.

### New in this pass (additive, safe to rely on)
`lensSetTheme(choice)` or write `data-theme` yourself, IntersectionObserver
`.reveal` behavior, `data-wiz-step`/`data-wiz-dot` wizard helper, `money()` /
`currency_symbol()` / `icon()` Jinja globals from `app/templating.py`.
