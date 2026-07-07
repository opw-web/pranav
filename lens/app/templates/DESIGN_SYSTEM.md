# LENS Design System (mobile-first)

Foundation for all screen work. Tokens live in `lens/app/static/css/input.css`
(Tailwind v4 `@theme`) and compile to `/static/css/app.css`. Shell lives in
`base.html`; JS helpers in `static/js/app.js`. **Prefer Tailwind utilities; use
the component classes below only where they cut real repetition.**

After editing `input.css`, rebuild: `bash lens/scripts/build_css.sh`.

Direction: calm, trustworthy fintech minimalism. Warm bone canvas, off-black ink
(never pure black), muted secondary text, hairline borders, PALE pastel accent
pairs. No gradients on surfaces, no neon, shadows barely-there.

---

## 1. Color tokens → utilities

Every token is a Tailwind color, so it works as `bg-*`, `text-*`, `border-*`.

| Utility base        | Hex / value            | Use                                   |
|---------------------|------------------------|---------------------------------------|
| `canvas`            | `#FBFBFA`              | page background (already on `<body>`) |
| `surface`           | `#FFFFFF`              | cards, bars, sheets                   |
| `subtle`            | `#F7F6F3`              | hover fills, skeletons, segment track |
| `ink`               | `#1A1A1A`              | primary text                          |
| `ink-soft`          | `#2F3437`              | headings / softer strong ink          |
| `muted`             | `#787774`              | secondary / helper text               |
| `faint`             | `#9B9A97`              | tertiary, placeholders, disabled      |
| `hair`              | `rgba(0,0,0,.06)`      | default hairline: `border-hair`       |
| `hair-strong`       | `#EAEAEA`              | opaque hairline (inputs)              |
| `brand` / `brand-ink` | `#1A1A1A` / `#FBFBFA` | primary button bg / its text          |

### Semantic accent PAIRS (background + `-ink` text). Always pair them.

| State           | bg utility          | text utility            |
|-----------------|---------------------|-------------------------|
| expense / negative | `bg-accent-red`   | `text-accent-red-ink`   |
| income / positive  | `bg-accent-green` | `text-accent-green-ink` |
| info / highlight   | `bg-accent-blue`  | `text-accent-blue-ink`  |
| warning / attention| `bg-accent-amber` | `text-accent-amber-ink` |

Example status pill: `<span class="chip bg-accent-green text-accent-green-ink">Income</span>`

> **Transaction amount sign colors** use `text-accent-red-ink` (expense) /
> `text-accent-green-ink` (income/refund) / `text-muted` (neutral/transfer).

### Fonts (system stacks only — never add CDN/Google fonts)
| Utility        | Stack purpose                                    |
|----------------|--------------------------------------------------|
| `font-sans`    | default UI (already on body)                     |
| `font-display` | **hero numbers / big headings** (editorial serif)|
| `font-mono`    | **transaction amounts**, keys, codes             |

### Radii
`rounded-control` (10px, buttons/inputs/chips) · `rounded-card` (14px, cards) ·
`rounded-sheet` (20px, sheet top corners). Standard `rounded-full` for pills/dots.

### Shadows
`shadow-card` (barely there) · `shadow-pop` (popovers) · `shadow-sheet` (sheet).
Do not exceed these.

---

## 2. Layout rules

- Content wrapper: `mx-auto max-w-5xl w-full px-4`. `base.html` already wraps
  `{% block content %}` — screens just emit content.
- Vertical rhythm inside a screen: `space-y-4` / `space-y-5`.
- Tap targets ≥ 44px (component classes enforce this; for custom controls add
  `min-h-[44px]`).
- The mobile tab bar is fixed; `<main>` already has `pb-28` clearance. Don't add
  your own bottom-fixed bars on mobile.
- Set the active tab from the router by passing `active_tab` in
  (`"home"`/`"txn"`/`"insights"`); optional. Set a mobile title via
  `{% block topbar_title %}Transactions{% endblock %}`.

### Responsive tables — REQUIRED pattern
Mobile shows **list-cards**; desktop (`md:+`) shows a **table**. Render both and
toggle with utilities:

```html
<!-- Mobile: stacked list-rows -->
<div class="md:hidden card divide-y divide-hair">
  {% for t in items %}
    {# list-row pattern from §4 #}
  {% endfor %}
</div>

<!-- Desktop: table -->
<div class="hidden md:block card overflow-x-auto">
  <table class="w-full text-sm">
    <tbody id="txn-tbody">{# existing txn_row.html rows #}</tbody>
  </table>
</div>
```
Keep `#txn-tbody` and `tr[id^='txn-row-']` intact for keyboard nav.

---

## 3. Buttons

```html
<button class="btn btn-primary">Save</button>
<button class="btn btn-secondary">Cancel</button>
<button class="btn btn-ghost">Skip</button>
```
Links styled as buttons: add the same classes to `<a>`. For a full-width mobile
CTA add `w-full`.

---

## 4. Patterns (copy-paste)

### Card
```html
<div class="card p-5">
  <p class="text-sm font-medium text-ink">Title</p>
  <p class="text-sm text-muted mt-1">Body…</p>
</div>
```

### Section header
```html
<div class="flex items-center justify-between mb-2">
  <h2 class="text-sm font-medium text-ink">Recent activity</h2>
  <a href="/txn" class="text-xs text-accent-blue-ink">all →</a>
</div>
```

### Mobile list-row (amount + category chip)
```html
<a class="list-row" hx-get="/txn/{{ t.id }}/edit" hx-target="…" hx-swap="outerHTML">
  <div class="min-w-0 flex-1">
    <p class="text-sm text-ink truncate">{{ t.merchant_clean or '—' }}</p>
    <p class="text-xs text-muted truncate">{{ t.txn_date }} · {{ t.account_name }}</p>
  </div>
  {# category chip — keep user color inline #}
  {% if t.category_name %}
  <span class="chip" style="background: {{ t.category_color }}22; color: {{ t.category_color }}">
    {{ t.category_name }}
  </span>
  {% endif %}
  <span class="font-mono text-sm whitespace-nowrap
    {{ 'text-accent-red-ink' if t.type == 'expense' else ('text-accent-green-ink' if t.type in ('income','refund') else 'text-muted') }}">
    {{ '-' if t.type == 'expense' else ('+' if t.type in ('income','refund') else '') }}{{ t.currency }} {{ "%.2f"|format(t.amount) }}
  </span>
</a>
```

### Category chip (user color preserved — do NOT theme-ify)
```html
<span class="chip" style="background: {{ color }}22; color: {{ color }}">{{ name }}</span>
<!-- Uncategorized fallback: -->
<span class="chip bg-subtle text-faint">Uncategorized</span>
```

### Hero number (dashboard)
```html
<p class="text-xs uppercase tracking-wide text-faint">Safe to spend</p>
<p class="font-display text-4xl text-ink mt-1">₹{{ "{:,.0f}".format(v) }}</p>
```

### Form field
```html
<label class="block text-xs text-muted mb-1">Amount</label>
<input name="amount" class="field" />
<!-- error variant: add these on the input -->
<input class="field border-accent-red-ink" aria-invalid="true" />
```

### Segmented control (e.g. This month / Last month)
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

### Empty state
```html
<div class="text-center py-16 max-w-sm mx-auto">
  <p class="font-display text-xl text-ink mb-1">No transactions yet</p>
  <p class="text-sm text-muted mb-6">Add your first one to get started.</p>
  <button onclick="lensToggleQuickadd()" class="btn btn-primary">Quick add</button>
</div>
```

### Loading skeleton (HTMX indicator or placeholder)
```html
<div class="space-y-2">
  <div class="skeleton h-4 w-2/3"></div>
  <div class="skeleton h-4 w-1/2"></div>
</div>
```

### Error state (inline)
```html
<div class="rounded-control bg-accent-red text-accent-red-ink text-sm px-3 py-2">
  Couldn't save — check the amount and try again.
</div>
```

### Toast (server-rendered — see `partials/toast.html`; do not change its ids)
The server emits toasts into `#toast-region` via `hx-swap-oob`. To match the
theme, a toast body uses: neutral `bg-ink text-brand-ink`, error
`bg-accent-red text-accent-red-ink`. Undo button: `underline`. (Editing the
toast partial is out of scope for screen agents — noted here for reference only.)

---

## 5. Do / Don't
- DO use accent pairs together; DON'T use a pale bg with dark-neutral text or vice-versa.
- DO keep amounts in `font-mono`; DON'T use `font-display` for anything but hero numbers / large headings.
- DON'T introduce new hex colors or shadows — use tokens.
- DON'T add CDN assets or web fonts.
- DON'T rename/remove the contract ids (`#quickadd-bar`, `#quickadd-preview`,
  `#quickadd-result`, `#learn-offer-region`, `#toast-region`, `#lens-cheatsheet`,
  `#txn-tbody`, `tr[id^='txn-row-']`) or the quick-add `hx-*` wiring.
```
