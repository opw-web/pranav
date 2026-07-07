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
