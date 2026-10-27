#!/usr/bin/env python3
"""Step 0: survey the model. Which shells are gold, what does the z histogram
of the gold geometry look like, and are there planar faces at z ~ 0?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from step_parse import Step

s = Step()
print(f"entities: {len(s.ent)}   cartesian points: {len(s.pt)}")
kinds = {}
for k in s.kind.values():
    kinds[k] = kinds.get(k, 0) + 1
for k, v in sorted(kinds.items(), key=lambda t: -t[1])[:18]:
    print(f"  {k:32s} {v}")

print("\n--- STYLED_ITEM colours ---")
si = s.styled_items()
seen = {}
for i, rgb, geo in si:
    key = tuple(round(c, 3) for c in rgb) if rgb else None
    seen.setdefault(key, []).append((i, geo))
for key, lst in sorted(seen.items(), key=lambda t: -len(t[1])):
    print(f"  rgb={key}  n_styled_items={len(lst)}")

# gold = high R, mid G, low B
def is_gold(rgb):
    if not rgb:
        return False
    r, g, b = rgb
    return r > 0.6 and g > 0.4 and b < 0.4 and r > b + 0.4

gold_roots = [geo for i, rgb, geo in si if is_gold(rgb)]
print(f"\ngold styled roots: {len(gold_roots)}  kinds="
      f"{sorted({s.kind.get(g) for g in gold_roots})}")

seen_ids = set()
gp = []
for g in gold_roots:
    for p in s.walk(g, "CARTESIAN_POINT"):
        if p not in seen_ids:
            seen_ids.add(p)
            gp.append(s.pt[p])
G = np.array(gp)
print(f"gold points: {len(G)}  bbox X[{G[:,0].min():.3f},{G[:,0].max():.3f}] "
      f"Y[{G[:,1].min():.3f},{G[:,1].max():.3f}] Z[{G[:,2].min():.3f},{G[:,2].max():.3f}]")

print("\ngold Z histogram (0.05 bins, only bins with n>0, z<1.0):")
zs = G[:, 2]
lo, hi = zs.min(), min(zs.max(), 1.0)
edges = np.arange(np.floor(lo * 20) / 20, hi + 0.05, 0.05)
h, e = np.histogram(zs, bins=edges)
for c, a, b in zip(h, e[:-1], e[1:]):
    if c:
        print(f"  z [{a:+.3f},{b:+.3f})  n={c}")

print("\nexact distinct gold z values with n>=8 (sorted):")
u, cnt = np.unique(np.round(zs, 4), return_counts=True)
for z, c in zip(u, cnt):
    if c >= 8:
        print(f"  z={z:+.4f}  n={c}")
