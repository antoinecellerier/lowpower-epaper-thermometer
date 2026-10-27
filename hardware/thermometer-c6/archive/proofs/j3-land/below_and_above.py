#!/usr/bin/env python3
"""Two loose ends:

(1) A proper census of everything the part puts BELOW the board (z<-0.15),
    clustered, so the NPTH post row is identified rather than assumed and any
    unexpected locating feature would show up.
(2) What sits ABOVE the heel-fillet region: the lowest material over
    y in [-4.45,-4.25] that is not the contact itself, i.e. how much vertical
    room a heel fillet has.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from step_parse import Step

s = Step()
P = np.array(list(s.pt.values()))


def clusters(v, tol):
    v = np.sort(v)
    out, cur = [], [v[0]]
    for x in v[1:]:
        if x - cur[-1] <= tol:
            cur.append(x)
        else:
            out.append(cur); cur = [x]
    out.append(cur)
    return [(float(np.mean(c)), float(min(c)), float(max(c)), len(c)) for c in out]


print("=== (1) below-board census (z < -0.15) ===")
sub = P[P[:, 2] < -0.15]
print(f"n={len(sub)}  z[{sub[:,2].min():.3f},{sub[:,2].max():.3f}]")
print("\n|x| clusters:")
for m, lo, hi, n in clusters(np.abs(sub[:, 0]), 0.20):
    sel = sub[np.abs(np.abs(sub[:, 0]) - m) < 0.30]
    print(f"  |x| ~ {m:6.3f}  [{lo:6.3f},{hi:6.3f}]  n={n:4d}   "
          f"y clusters: " + ", ".join(
              f"{a:+.3f}(n={c})" for a, _, _, c in clusters(sel[:, 1], 0.35)))

print("\nper below-board feature, bbox:")
feat = [("shell leg", 4.0, 4.6), ("NPTH post", 2.6, 3.2),
        ("other |x| 3.0-3.4", 3.0, 3.4)]
for lbl, a, b in feat:
    sel = sub[(np.abs(sub[:, 0]) >= a) & (np.abs(sub[:, 0]) <= b)]
    if not len(sel):
        print(f"  {lbl}: none"); continue
    print(f"  {lbl}: n={len(sel)}  |x|[{np.abs(sel[:,0]).min():.3f},"
          f"{np.abs(sel[:,0]).max():.3f}]  z[{sel[:,2].min():.3f},{sel[:,2].max():.3f}]")
    for m, lo, hi, n in clusters(sel[:, 1], 0.35):
        s2 = sel[np.abs(sel[:, 1] - m) < 0.5]
        print(f"      y row {m:+7.3f} [{lo:+7.3f},{hi:+7.3f}] n={n}  "
              f"|x| ctr {(np.abs(s2[:,0]).min()+np.abs(s2[:,0]).max())/2:.4f}  "
              f"z[{s2[:,2].min():.3f},{s2[:,2].max():.3f}]")

# the NPTH post: round, so take the cylindrical surfaces below the board
print("\n  NPTH post from its cylindrical surface(s):")
import re
for i, b in s.ent.items():
    if s.kind.get(i) != "CYLINDRICAL_SURFACE":
        continue
    ar = s.refs[s.refs[i][0]] if s.kind.get(s.refs[i][0]) == "AXIS2_PLACEMENT_3D" else None
    ax = s.refs[i][0]
    if s.kind.get(ax) != "AXIS2_PLACEMENT_3D":
        continue
    arr = s.refs[ax]
    org, d = s.pt.get(arr[0]), s.dir.get(arr[1]) if len(arr) > 1 else None
    rad = float(re.findall(r",\s*([-+0-9.Ee]+)\s*\)\s*;?\s*$", s.ent[i])[0])
    if org is None or d is None:
        continue
    if abs(abs(d[2]) - 1) < 1e-3 and org[2] < 0.3 and 2.0 < abs(org[0]) < 3.4:
        print(f"    #{i} r={rad:.4f} origin=({org[0]:+.4f},{org[1]:+.4f},{org[2]:+.4f})")

print("\n=== (2) room above the heel-fillet region ===")
print("contacts occupy |x|<=3.425; bend arc spans y[-4.450,-4.250], "
      "tail top surface z=0.200 (flat part) rising to the vertical riser.")
win = P[(np.abs(P[:, 0]) <= 3.45) & (P[:, 1] > -4.50) & (P[:, 1] < -4.20)]
print(f"all points over the bend window: n={len(win)}")
for m, lo, hi, n in clusters(win[:, 2], 0.05):
    sel = win[np.abs(win[:, 2] - m) < 0.08]
    print(f"  z ~ {m:+7.3f} [{lo:+7.3f},{hi:+7.3f}] n={n:4d}  "
          f"|x|[{np.abs(sel[:,0]).min():.3f},{np.abs(sel[:,0]).max():.3f}]")

print("\nlowest material spanning the FULL contact row (|x| up to >3.0) "
      "in y[-4.7,-3.5], excluding the contacts themselves (z>0.25):")
w2 = P[(np.abs(P[:, 0]) <= 3.45) & (P[:, 1] > -4.70) & (P[:, 1] < -3.50)
       & (P[:, 2] > 0.25) & (P[:, 2] < 3.0)]
for m, lo, hi, n in clusters(w2[:, 2], 0.06):
    sel = w2[np.abs(w2[:, 2] - m) < 0.08]
    print(f"  z ~ {m:+7.3f} n={n:4d}  |x|[{np.abs(sel[:,0]).min():.3f},"
          f"{np.abs(sel[:,0]).max():.3f}]  y[{sel[:,1].min():+.3f},{sel[:,1].max():+.3f}]")
