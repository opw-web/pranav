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
