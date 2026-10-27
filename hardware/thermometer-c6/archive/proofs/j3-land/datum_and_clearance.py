#!/usr/bin/env python3
"""(a) Re-derive the model's own datum chain from scratch (front peg axis),
(b) check whether anything non-gold overhangs the heel-fillet region.

(a) matters because every "behind the front shell slot" number in the verdict
    is measured from the front peg axis in the model frame.
(b) matters because a heel fillet can only form if the space above the bend
    arc is open.  Only ADVANCED_FACE styled roots are used, so the walk cannot
    leak into shared assembly-level entities (which is what makes a naive
    colour walk report the whole model).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from step_parse import Step


def is_gold(rgb):
    if not rgb:
        return False
    r, g, b = rgb
    return r > 0.6 and g > 0.4 and b < 0.4 and r > b + 0.4


s = Step()
si = s.styled_items()
face_roots = [(rgb, geo) for _, rgb, geo in si if s.kind.get(geo) == "ADVANCED_FACE"]
print(f"styled ADVANCED_FACE roots: {len(face_roots)} of {len(si)} styled items")
byc = {}
for rgb, geo in face_roots:
    byc.setdefault(tuple(round(c, 3) for c in rgb) if rgb else None, []).append(geo)
print("  colours:", {k: len(v) for k, v in byc.items()})

# ---------------------------------------------------------------- (a) datum
P = np.array(list(s.pt.values()))
print(f"\n=== (a) model datum chain, re-derived ===")
barrel = P[(P[:, 2] > -0.55) & (P[:, 2] < -0.35)]
print(f"below-board barrel slice z[-0.55,-0.35]: n={len(barrel)}")
legs = barrel[np.abs(barrel[:, 0]) > 3.6]
print(f"  shell legs |x|>3.6: n={len(legs)}  |x| range "
      f"[{np.abs(legs[:,0]).min():.3f},{np.abs(legs[:,0]).max():.3f}]")
for lbl, sel in (("front", legs[legs[:, 1] > -2.0]), ("rear", legs[legs[:, 1] <= -2.0])):
    print(f"    {lbl} leg row: y [{sel[:,1].min():+.3f},{sel[:,1].max():+.3f}] "
          f"centre {(sel[:,1].min()+sel[:,1].max())/2:+.4f}  n={len(sel)}")
front_y = (legs[legs[:, 1] > -2.0][:, 1].min() + legs[legs[:, 1] > -2.0][:, 1].max()) / 2
rear_y = (legs[legs[:, 1] <= -2.0][:, 1].min() + legs[legs[:, 1] <= -2.0][:, 1].max()) / 2
sub = P[P[:, 2] < -0.15]
post = sub[(np.abs(sub[:, 0]) > 2.4) & (np.abs(sub[:, 0]) < 3.4)]
post_y = (post[:, 1].min() + post[:, 1].max()) / 2
print(f"  NPTH posts |x| in (2.4,3.4): y centre {post_y:+.4f}  "
      f"|x| ctr {np.abs(post[:,0]).mean():.4f}  n={len(post)}")

print(f"\n  CHAIN, front peg axis = 0, +ve = away from the mouth:")
print(f"    front peg          {0.0:8.4f}")
print(f"    rear peg           {front_y - rear_y:8.4f}   (drawing 4.1716)")
print(f"    NPTH post          {front_y - post_y:8.4f}   (drawing 3.6716)")
print(f"    foot heel          {front_y - (-4.450):8.4f}   (measured face edge)")
print(f"    foot toe           {front_y - (-5.300):8.4f}   (measured face edge)")

# ------------------------------------------------------- (b) heel clearance
print("\n=== (b) non-gold material near the feet (y in [-5.40,-4.00], z<1.0) ===")
for key, roots in byc.items():
    if key and is_gold(key):
        continue
    seen, pts = set(), []
    for g in roots:
        for p in s.walk(g, "CARTESIAN_POINT"):
            if p not in seen:
                seen.add(p)
                pts.append(s.pt[p])
    C = np.array(pts)
    sel = C[(C[:, 1] > -5.40) & (C[:, 1] < -4.00) & (C[:, 2] < 1.0)]
    print(f"\n colour {key}: {len(roots)} faces, {len(C)} pts; in window: {len(sel)}")
    if len(sel):
        print(f"   x[{sel[:,0].min():+.3f},{sel[:,0].max():+.3f}] "
              f"y[{sel[:,1].min():+.3f},{sel[:,1].max():+.3f}] "
              f"z[{sel[:,2].min():+.3f},{sel[:,2].max():+.3f}]")
        inner = sel[np.abs(sel[:, 0]) <= 3.5]
        print(f"   of those, within the contact x-band |x|<=3.5: {len(inner)}")
        if len(inner):
            print(f"     x[{inner[:,0].min():+.3f},{inner[:,0].max():+.3f}] "
                  f"y[{inner[:,1].min():+.3f},{inner[:,1].max():+.3f}] "
                  f"z[{inner[:,2].min():+.3f},{inner[:,2].max():+.3f}]")
            for p in sorted(inner.tolist(), key=lambda q: (q[1], q[0]))[:24]:
                print(f"       ({p[0]:+.3f},{p[1]:+.3f},{p[2]:+.3f})")

# rear-most low-lying body face inside the contact band, whatever colour
print("\n=== rear-most non-gold face vertex with |x|<3.5 and z<1.0 ===")
allpts = []
for key, roots in byc.items():
    if key and is_gold(key):
        continue
    seen = set()
    for g in roots:
        for p in s.walk(g, "CARTESIAN_POINT"):
            if p not in seen:
                seen.add(p)
                allpts.append(s.pt[p])
A = np.array(allpts)
A = A[(np.abs(A[:, 0]) < 3.5) & (A[:, 2] < 1.0)]
print(f"  n={len(A)}  min y = {A[:,1].min():+.4f}  "
      f"(foot heel is at y=-4.450, bend arc ends at y=-4.250)")
low = A[A[:, 1] < -3.5]
if len(low):
    print(f"  vertices with y<-3.5: n={len(low)}  "
          f"y[{low[:,1].min():+.3f},{low[:,1].max():+.3f}] "
          f"z[{low[:,2].min():+.3f},{low[:,2].max():+.3f}]")
