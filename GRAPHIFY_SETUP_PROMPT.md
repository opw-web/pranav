# Paste-into-Claude prompt: set up graphify like the NIO project

Copy everything in the fenced block below into a fresh Claude Code session in the
other project's root.

---

```
Set up graphify (knowledge-graph + always-on hooks + auto-refresh + Obsidian vault)
in THIS project, exactly the way it's configured in my NIO project. Do all of it,
verifying each step. Here is the full spec — follow it precisely, including the
gotchas, which are not optional.

GOAL
- A queryable code knowledge graph in ./graphify-out/ (graph.json, GRAPH_REPORT.md).
- Labeled communities (human-readable names, not "Community 0/1/2").
- An Obsidian vault at ./graphify-out/obsidian/ (open THAT folder in Obsidian).
- PreToolUse hooks that push you to consult the graph before grep/read.
- A PostToolUse hook that auto-rebuilds + re-labels + re-vaults after your edits.
- Everything stays under ./graphify-out/, updated in place, with NO dated backup folders.
- ONLY real source in the graph — backups, vendored/minified/compiled bundles, and
  generated output excluded via a .graphifyignore, so the graph never fills with junk.

GOTCHAS (these cost a previous session hours — honor them)
1. The command that installs the project hooks is `graphify claude install`
   (writes ./CLAUDE.md + the real PreToolUse hooks). `graphify install --platform
   claude` only installs the GLOBAL skill + ~/.claude/CLAUDE.md and NO hook. Run
   both: the platform one first (for the /graphify skill), then `graphify claude install`.
2. This Claude Code version exposes NO dedicated Grep/Glob tools — search routes
   through Bash. So the working hooks match "Bash" (inspecting the command for
   grep/rg/find/fd) and "Read|Glob". `graphify claude install` writes these
   correctly. Do NOT hand-write a matcher on "Glob|Grep" — it never fires here.
3. graphify's PARALLEL AST extraction can crash on macOS ("process pool terminated
   abruptly", yields 0 edges). Build the FULL graph SERIALLY with parallel=False.
   Incremental `graphify update .` is safe (it runs serially under ~20 changed files).
4. Community labeling needs an LLM. If GEMINI_API_KEY/GOOGLE_API_KEY is unset but the
   `claude` CLI is installed, use `--backend=claude-cli`. Each label run = one Claude call.
5. graphify auto-creates a dated backup folder (graphify-out/<date>/) before overwrites
   once labels are curated. Set GRAPHIFY_NO_BACKUP=1 to keep ./graphify-out/ clean.
6. graphify indexes EVERYTHING not ignored. It honors .gitignore + auto-skips
   node_modules/.git/venvs, but committed junk (backup dirs, minified/compiled JS,
   vendored code, generated output) WILL pollute the graph — producing dozens of
   garbage communities like "Minified Extension Code" / "Obfuscated Symbols". Create a
   .graphifyignore BEFORE building (Step 2) to exclude it. This is the single biggest
   cause of a useless graph.

STEPS

1) Install:
   pip install graphifyy
   graphify install --platform claude     # global /graphify skill + ~/.claude/CLAUDE.md
   graphify claude install                # project ./CLAUDE.md + PreToolUse hooks in .claude/settings.json

2) FIRST, exclude junk so it never enters the graph. Create .graphifyignore in the
   project root (graphify reads it like .gitignore — it MUST exist before the build).
   Start from these common patterns, then ADD this project's own backup/data/snapshot
   dirs (look around the repo: anything like data.bak/, backups/, dumps/, vendored libs,
   *_compiled.js, build output). Inspect the tree and tailor it — don't just paste blindly.

   ----- .graphifyignore -----
   # Keep the knowledge graph to real source — exclude backups, vendored code,
   # minified/compiled bundles, and generated output.
   **/*.min.js
   **/*.min.css
   **/*_compiled.js
   **/*.bundle.js
   **/dist/
   **/build/
   **/out/
   **/.next/
   **/coverage/
   **/vendor/
   **/__generated__/
   **/*.generated.*
   # --- ADD project-specific junk dirs below, e.g.: ---
   # data.bak/
   # data/
   # backups/
   ----- end -----

   After the first build (Step 7), sanity-check the community names: if you see clusters
   named "Minified …", "Obfuscated …", "WASM …", or anything from a backup/build dir,
   add those paths to .graphifyignore and rebuild (re-run Steps 3→5). Goal: every community
   name should map to a real part of the codebase.

3) Build the graph SERIALLY (no LLM). Create scratch script and run it from the project root:

   ----- build_graph.py -----
   import json
   from pathlib import Path
   from graphify.detect import detect
   from graphify.extract import collect_files, extract
   from graphify.build import build_from_json
   from graphify.cluster import cluster, score_all
   from graphify.analyze import god_nodes, surprising_connections, suggest_questions
   from graphify.report import generate
   from graphify.export import to_json
   ROOT="."; out=Path("graphify-out"); out.mkdir(exist_ok=True)
   import sys; (out/".graphify_python").write_text(sys.executable); (out/".graphify_root").write_text(".")
   det=detect(Path(ROOT)); (out/".graphify_detect.json").write_text(json.dumps(det,ensure_ascii=False))
   files=det.get("files",{}); code=[]
   for f in files.get("code",[]):
       p=Path(f); code+= (collect_files(p) if p.is_dir() else [p])
   if not code: raise SystemExit("no code files")
   ex=extract(code, cache_root=Path(ROOT), parallel=False)   # parallel=False is REQUIRED
   G=build_from_json(ex, root=ROOT, directed=False)
   if G.number_of_nodes()==0: raise SystemExit("empty graph")
   comm=cluster(G); coh=score_all(G,comm)
   labels={c:"Community "+str(c) for c in comm}
   to_json(G,comm,"graphify-out/graph.json")
   rep=generate(G,comm,coh,labels,god_nodes(G),surprising_connections(G,comm),det,
                {"input":0,"output":0},ROOT,suggested_questions=suggest_questions(G,comm,labels))
   Path("graphify-out/GRAPH_REPORT.md").write_text(rep)
   print("built", G.number_of_nodes(),"nodes", G.number_of_edges(),"edges")
   ----- end -----

   Run with: OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES python3 build_graph.py
   (If the corpus has many docs/images you may instead run /graphify . for semantic
   extraction, but code-only serial build above is the reliable baseline.)

4) Label communities (real names):
   GRAPHIFY_NO_BACKUP=1 graphify label . --backend=claude-cli
   (On a fresh build every community is a placeholder, so label ALL — drop --missing-only.
    If GEMINI_API_KEY is set, drop --backend to use Gemini instead.)

5) Create .claude/graphify/make_vault.py with EXACTLY this content:

   ----- .claude/graphify/make_vault.py -----
   import json
   from pathlib import Path
   from networkx.readwrite import json_graph
   from graphify.export import to_obsidian
   OUT=Path("graphify-out")
   raw=json.loads((OUT/"graph.json").read_text(encoding="utf-8"))
   G=json_graph.node_link_graph(raw, edges="links")
   communities={}
   for nid,data in G.nodes(data=True):
       cid=data.get("community")
       if cid is None: continue
       communities.setdefault(int(cid),[]).append(nid)
   community_labels={}
   lp=OUT/".graphify_labels.json"
   if lp.exists():
       lr=json.loads(lp.read_text(encoding="utf-8"))
       src=lr.get("labels",lr) if isinstance(lr,dict) else {}
       for k,v in src.items():
           try: community_labels[int(k)]=v if isinstance(v,str) else (v.get("name") if isinstance(v,dict) else str(v))
           except (ValueError,TypeError): pass
   n=to_obsidian(G,communities,str(OUT/"obsidian"),community_labels=community_labels)
   print(f"Wrote {n} notes ({len(communities)} communities, {len(community_labels)} labels)")
   ----- end -----

   Then run it once: python3 .claude/graphify/make_vault.py

6) Create .claude/graphify/refresh.sh with EXACTLY this content, and chmod +x it:

   ----- .claude/graphify/refresh.sh -----
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
   ----- end -----

7) Register the PostToolUse auto-refresh hook. Read .claude/settings.json (created by
   `graphify claude install`), and add this entry under hooks.PostToolUse (create the
   array if absent), WITHOUT touching the existing PreToolUse hooks:

   {
     "matcher": "Write|Edit|MultiEdit",
     "hooks": [
       { "type": "command",
         "command": "nohup bash \"$CLAUDE_PROJECT_DIR/.claude/graphify/refresh.sh\" >/dev/null 2>&1 </dev/null & exit 0" }
     ]
   }

   Do this in Python (json load/dump) to keep the file valid; do not hand-edit the
   escaped PreToolUse command strings.

8) Verify and report:
   - .claude/settings.json has PreToolUse matchers ["Bash","Read|Glob"] and
     PostToolUse matcher ["Write|Edit|MultiEdit"], and is valid JSON.
   - graphify-out/ contains graph.json, GRAPH_REPORT.md, and obsidian/ (with
     obsidian/.obsidian/graph.json present). No dated <date>/ folder.
   - NO community is named after minified/backup/generated code (if any are, fix
     .graphifyignore and rebuild per Step 2).
   - `graphify query "what does this project do"` returns nodes.
   - Tell me to RESTART Claude Code once so the new hooks load (approve them when prompted),
     and to open ./graphify-out/obsidian/ as the Obsidian vault.

Notes for me afterward: auto-refresh only fires on YOUR (Claude's) edits, is debounced
to 180s, and only calls the LLM labeler when the node count changed. If I edit files
outside Claude, I run `bash .claude/graphify/refresh.sh` manually to resync. Deleting
code needs a forced full rebuild (graphify won't shrink the graph automatically).
The .graphifyignore keeps junk out permanently — both rebuilds and the auto-refresh
read it — so if I ever see garbage communities, I add a pattern there and rebuild.
```
