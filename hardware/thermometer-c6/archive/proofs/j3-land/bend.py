#!/usr/bin/env python3
"""Resolve the gold material found at z=0, y=-4.250 (forward of the foot heel).

If part of the tail touches the board plane beyond the 12 measured planar
faces, the "foot" is longer than those faces and the whole coverage analysis
changes.  So: enumerate every gold face that owns a vertex at z~0, classify it,
and reconstruct the tail's true bottom profile in the y-z plane.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from step_parse import Step
import re


def is_gold(rgb):
    if not rgb:
        return False
    r, g, b = rgb
    return r > 0.6 and g > 0.4 and b < 0.4 and r > b + 0.4


s = Step()
gold = [geo for _, rgb, geo in s.styled_items()
        if is_gold(rgb) and s.kind.get(geo) == "ADVANCED_FACE"]

print("=== every gold face with a vertex at |z| < 0.01 ===")
print(f"{'face':>7} {'surf':>22} {'normal/axis':>26} "
      f"{'x range':>18} {'y range':>18} {'z range':>18}")
touch = []
for f in gold:
    i = s.face_info(f)
    v = i["verts"]
    if not len(v) or np.abs(v[:, 2]).min() > 0.01:
        continue
    touch.append(i)
    n = i["normal"]
    if n is None:
        # cylinder: report its axis + radius
        surf = s.refs[f][-1]
        ax = s.refs[surf][0]
        ar = s.refs[ax]
        d = s.dir.get(ar[1])
        rad = re.findall(r"[-+0-9.Ee]+\s*\)\s*;?\s*$", s.ent[surf])
        radv = float(re.findall(r",\s*([-+0-9.Ee]+)\s*\)\s*;?\s*$", s.ent[surf])[0])
        ntxt = f"axis({d[0]:+.2f},{d[1]:+.2f},{d[2]:+.2f}) r={radv:.3f}"
        org = s.pt.get(ar[0])
        ntxt += f" o=({org[0]:+.2f},{org[1]:+.2f},{org[2]:+.2f})"
    else:
        ntxt = f"({n[0]:+.3f},{n[1]:+.3f},{n[2]:+.3f})"
    print(f"{f:7d} {i['surf']:>22} {ntxt:>26} "
          f"[{v[:,0].min():+7.3f},{v[:,0].max():+7.3f}] "
          f"[{v[:,1].min():+7.3f},{v[:,1].max():+7.3f}] "
          f"[{v[:,2].min():+7.3f},{v[:,2].max():+7.3f}]")

print(f"\ntotal gold faces touching z=0: {len(touch)}")

print("\n=== all 12 gold CYLINDRICAL_SURFACE faces ===")
for f in gold:
    i = s.face_info(f)
    if i["surf"] != "CYLINDRICAL_SURFACE":
        continue
    surf = s.refs[f][-1]
    ar = s.refs[s.refs[surf][0]]
    org, d = s.pt.get(ar[0]), s.dir.get(ar[1])
    radv = float(re.findall(r",\s*([-+0-9.Ee]+)\s*\)\s*;?\s*$", s.ent[surf])[0])
    v = i["verts"]
    print(f"  #{f} r={radv:.4f} axis=({d[0]:+.2f},{d[1]:+.2f},{d[2]:+.2f}) "
          f"origin=({org[0]:+.4f},{org[1]:+.4f},{org[2]:+.4f})  "
          f"verts y[{v[:,1].min():+.3f},{v[:,1].max():+.3f}] "
          f"z[{v[:,2].min():+.3f},{v[:,2].max():+.3f}]")

print("\n=== ONE contact: every gold face whose x-range lies within [-0.45,-0.05] ===")
print("    (the A/B contact at xc=-0.250, w=0.200 -- its complete face list)")
for f in gold:
    i = s.face_info(f)
    v = i["verts"]
    if not len(v):
        continue
    if v[:, 0].min() >= -0.46 and v[:, 0].max() <= -0.04:
        n = i["normal"]
        ntxt = "-" if n is None else f"({n[0]:+.2f},{n[1]:+.2f},{n[2]:+.2f})"
        print(f"  #{f:6d} {i['surf']:>22} n={ntxt:>20} "
              f"y[{v[:,1].min():+7.3f},{v[:,1].max():+7.3f}] "
              f"z[{v[:,2].min():+7.3f},{v[:,2].max():+7.3f}]  verts:")
        for p in sorted(v.tolist(), key=lambda q: (q[1], q[2], q[0])):
            print(f"        ({p[0]:+.4f},{p[1]:+.4f},{p[2]:+.4f})")
