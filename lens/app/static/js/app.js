// Category picker selection (§5.2). One picker fragment (Task 5), three call sites:
// - categories.html demo: no target set, just shows "Selected: …"
// - a transaction row's edit mode (Task 6): target={type:"txn", id} -> PATCH the row immediately
// - the new-transaction form (Task 6): target={type:"new", idFieldId, labelFieldId} -> fill hidden inputs
// Task 7's quick-add bar reuses the same "new" pattern.
window.lensCategoryTarget = null;

function lensApplyCategorySelection(id, name) {
    const target = window.lensCategoryTarget;
    if (target && target.type === "txn") {
        htmx.ajax("PATCH", `/txn/${target.id}`, {
            target: `#txn-row-${target.id}`,
            swap: "outerHTML",
            values: { category_id: id },
        });
        window.lensCategoryTarget = null;
        return;
    }
    if (target && target.type === "new") {
        const idInput = document.getElementById(target.idFieldId);
        const labelEl = document.getElementById(target.labelFieldId);
        if (idInput) idInput.value = id;
        if (labelEl) labelEl.textContent = name;
        window.lensCategoryTarget = null;
        return;
    }
    const out = document.getElementById("category-picker-selection");
    if (out) out.textContent = `Selected: ${name}`;
    document.dispatchEvent(new CustomEvent("category-selected", { detail: { id, name } }));
}
function lensSelectCategory(el) {
    lensApplyCategorySelection(el.getAttribute("data-category-id"), el.getAttribute("data-category-name"));
}

// Quick-add keyword-prefix suggestion chip (§WS4b): tapping "fuel -> Utilities"
// sets the hidden category_override_id field (the single source of truth the
// >/!  forced-category token also resolves through server-side - see
// _resolve_category_override in quickadd.py) and re-fetches the preview so the
// resolved category updates immediately. A real keystroke in the bar (below)
// clears the override again so a later edit isn't silently pinned to a stale tap.
function lensQuickaddSuggest(el) {
    const id = el.getAttribute("data-category-id");
    const override = document.getElementById("quickadd-category-override-id");
    const bar = document.getElementById("quickadd-bar");
    if (override) override.value = id;
    if (bar) {
        htmx.ajax("POST", "/txn/quickadd/preview", {
            target: "#quickadd-preview",
            swap: "innerHTML",
            source: bar,
        });
    }
}
// Uses "input" (fires only when the field's value actually changes - typing,
// backspace, paste) rather than "keydown" (fires on every key, including the
// bare Enter that submits the form). The form has no submit button - Enter in
// this input is the only way to commit - so a "keydown" listener here would
// clear the override on that very Enter press, before the browser serializes
// the form, silently discarding a tapped suggestion chip. "input" leaves the
// override intact through Enter-to-submit while still clearing it the moment
// the reason text is actually edited to something else.
document.getElementById("quickadd-bar")?.addEventListener("input", () => {
    const override = document.getElementById("quickadd-category-override-id");
    if (override && override.value) override.value = "";
});

// Full keyboard map (§5.1): a add · / search · j/k move · e edit · c set category ·
// t tag · x select · u undo · ? cheatsheet. Row navigation walks the transaction table.
let lensActiveRow = null;

function lensRows() {
    return Array.from(document.querySelectorAll("#txn-tbody tr[id^='txn-row-']"));
}
function lensHighlight(row) {
    lensRows().forEach((r) => r.classList.remove("ring-2", "ring-neutral-400"));
    if (row) {
        row.classList.add("ring-2", "ring-neutral-400");
        row.scrollIntoView({ block: "nearest" });
        lensActiveRow = row;
    }
}
function lensMove(delta) {
    const rows = lensRows();
    if (!rows.length) return;
    let idx = rows.indexOf(lensActiveRow);
    idx = idx === -1 ? 0 : Math.min(rows.length - 1, Math.max(0, idx + delta));
    lensHighlight(rows[idx]);
}
function lensRowId(row) {
    return row ? row.id.replace("txn-row-", "") : null;
}

document.addEventListener("keydown", (e) => {
    const tag = (e.target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable;

    if (e.key === "Escape") {
        document.getElementById("lens-cheatsheet")?.classList.add("hidden");
    }

    if (typing) {
        if (e.key === "Escape") e.target.blur();
        return;
    }

    switch (e.key) {
        case "a":
            e.preventDefault();
            document.getElementById("quickadd-bar")?.focus();
            break;
        case "/":
            e.preventDefault();
            document.querySelector("[name='q']")?.focus() || document.getElementById("quickadd-bar")?.focus();
            break;
        case "j":
            e.preventDefault();
            lensMove(1);
            break;
        case "k":
            e.preventDefault();
            lensMove(-1);
            break;
        case "e":
        case "c": // set category = open the row editor where the category picker lives
            if (lensActiveRow) {
                e.preventDefault();
                htmx.ajax("GET", `/txn/${lensRowId(lensActiveRow)}/edit`, {
                    target: `#${lensActiveRow.id}`, swap: "outerHTML",
                });
            }
            break;
        case "t": // tag: open editor and focus the tags field
            if (lensActiveRow) {
                e.preventDefault();
                const id = lensRowId(lensActiveRow);
                htmx.ajax("GET", `/txn/${id}/edit`, { target: `#${lensActiveRow.id}`, swap: "outerHTML" }).then(() => {
                    document.querySelector(`#txn-row-${id} input[name='tags']`)?.focus();
                });
            }
            break;
        case "x": // toggle-select the active row's checkbox
            if (lensActiveRow) {
                e.preventDefault();
                const cb = lensActiveRow.querySelector("input[type='checkbox']");
                if (cb) cb.checked = !cb.checked;
            }
            break;
        case "u": // undo: click the most recent toast's Undo button
            {
                const undoBtn = document.querySelector("#toast-region button");
                if (undoBtn) { e.preventDefault(); undoBtn.click(); }
            }
            break;
        case "?":
            e.preventDefault();
            document.getElementById("lens-cheatsheet")?.classList.toggle("hidden");
            break;
    }
});

// ============================================================================
// Mobile shell helpers (added for the mobile-first redesign; everything above
// is unchanged). Bottom-sheet open/close + the slide-up quick-add.
// ============================================================================

// Reveal a bottom sheet / dialog by id (removes the `hidden` class).
function lensOpenSheet(id) {
    document.getElementById(id)?.classList.remove("hidden");
}

// Hide a bottom sheet / dialog by id.
function lensCloseSheet(id) {
    document.getElementById(id)?.classList.add("hidden");
}

// Reveal the mobile slide-up quick-add panel and focus the input.
// On md:+ the panel is always visible (Tailwind `md:flex` wins over `hidden`),
// so this simply focuses the bar.
function lensToggleQuickadd() {
    document.getElementById("quickadd-shell")?.classList.remove("hidden");
    const bar = document.getElementById("quickadd-bar");
    if (bar) { bar.focus(); bar.select?.(); }
}

// Ensure the keyboard `a` shortcut also un-hides the mobile quick-add panel
// BEFORE the existing focus handler runs (capture phase). Augments — does not
// replace — the main keydown listener above.
document.addEventListener("keydown", (e) => {
    if (e.key !== "a") return;
    const tag = (e.target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable;
    if (typing) return;
    document.getElementById("quickadd-shell")?.classList.remove("hidden");
}, true);

// Esc closes the "More" sheet and, on mobile, collapses an empty quick-add panel.
document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    document.getElementById("more-sheet")?.classList.add("hidden");
    const shell = document.getElementById("quickadd-shell");
    const bar = document.getElementById("quickadd-bar");
    if (shell && bar && !bar.value) {
        shell.classList.add("hidden");
    }
});

// ============================================================================
// Theme (light / dark / system), written to `data-theme` + localStorage so
// the CSS `:root[data-theme="dark"]` / `[data-theme="light"]` overrides in
// input.css win over the OS `prefers-color-scheme` in both directions.
// ============================================================================
const LENS_THEME_KEY = "lens-theme";

function lensSetTheme(choice) {
    if (choice === "system") {
        document.documentElement.removeAttribute("data-theme");
        try { localStorage.removeItem(LENS_THEME_KEY); } catch (e) {}
    } else {
        document.documentElement.setAttribute("data-theme", choice);
        try { localStorage.setItem(LENS_THEME_KEY, choice); } catch (e) {}
    }
    lensReflectThemeChoice();
}

function lensReflectThemeChoice() {
    let current = "system";
    try { current = localStorage.getItem(LENS_THEME_KEY) || "system"; } catch (e) {}
    document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
        const active = btn.getAttribute("data-theme-choice") === current;
        btn.classList.toggle("is-active", active);
        btn.setAttribute("aria-selected", active ? "true" : "false");
    });
}

function lensInitTheme() {
    // The inline <script> in base.html already applies the saved theme before
    // paint (avoids a flash); this just syncs the More-sheet segment UI.
    lensReflectThemeChoice();
}

document.addEventListener("DOMContentLoaded", lensInitTheme);

// ============================================================================
// Scroll-reveal: fades/slides `.reveal` elements in once they enter the
// viewport. Respects prefers-reduced-motion via the CSS rule that neutralizes
// the transition; the class toggle itself is harmless either way.
// ============================================================================
if ("IntersectionObserver" in window) {
    const lensRevealObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    lensRevealObserver.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );

    function lensObserveReveals() {
        document.querySelectorAll(".reveal:not(.is-visible)").forEach((el) => lensRevealObserver.observe(el));
    }

    document.addEventListener("DOMContentLoaded", lensObserveReveals);
    // Re-scan after HTMX swaps content in (new `.reveal` nodes from partials).
    document.body.addEventListener("htmx:afterSwap", lensObserveReveals);
} else {
    // No IO support: just show everything.
    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
    });
}

// ============================================================================
// Wizard step helper (multi-step forms, e.g. the import wizard). Shows the
// step whose element has `data-wiz-step === n` and hides the rest; toggles
// a matching `.segment-item`/progress dot with `data-wiz-dot === n` if present.
// ============================================================================
function lensWizStep(n) {
    document.querySelectorAll("[data-wiz-step]").forEach((el) => {
        const step = Number(el.getAttribute("data-wiz-step"));
        el.classList.toggle("hidden", step !== Number(n));
    });
    document.querySelectorAll("[data-wiz-dot]").forEach((el) => {
        const step = Number(el.getAttribute("data-wiz-dot"));
        el.classList.toggle("is-active", step === Number(n));
    });
}
