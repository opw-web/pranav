#!/usr/bin/env bash
# graphify auto-refresh: incremental re-extract -> label NEW communities -> rebuild vault.
set -uo pipefail
DEBOUNCE=180
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$ROOT" 2>/dev/null || exit 0
[ -f graphify-out/graph.json ] || exit 0
LOCK="graphify-out/.refresh.lock"; STAMP="graphify-out/.refresh.stamp"
now=$(date +%s)
if [ -f "$STAMP" ]; then last=$(cat "$STAMP" 2>/dev/null || echo 0); [ $((now-last)) -lt "$DEBOUNCE" ] && exit 0; fi
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT
echo "$now" > "$STAMP"
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export GRAPHIFY_NO_BACKUP=1
PY=$(cat graphify-out/.graphify_python 2>/dev/null || echo python3)
count() { "$PY" -c "import json;print(len(json.load(open('graphify-out/graph.json'))['nodes']))" 2>/dev/null || echo 0; }
before=$(count)
graphify update . >/dev/null 2>&1 || true
after=$(count)
if [ "$before" != "$after" ]; then
  graphify label . --backend=claude-cli --missing-only >/dev/null 2>&1 || true
  "$PY" "$ROOT/.claude/graphify/make_vault.py" >/dev/null 2>&1 || true
fi
exit 0
