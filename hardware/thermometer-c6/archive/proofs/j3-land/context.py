#!/usr/bin/env python3
"""Cross-checks around the measured feet.

  * is there ANY gold material at z < 0.05 outside the 12 measured faces?
    (i.e. did the PLANE/z=0 filter miss part of the contacting surface?)
  * where does each tail rise?  z profile of the gold as a function of y.
  * where is the rear face of the plastic body / shell relative to the foot
    heel?  (decides whether a heel fillet can physically form)
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

groups = {}
for _, rgb, geo in si:
    key = tuple(round(c, 3) for c in rgb) if rgb else None
    groups.setdefault(key, []).append(geo)

def cloud(roots):
    seen, out = set(), []
    for g in roots:
        for p in s.walk(g, "CARTESIAN_POINT"):
            if p not in seen:
                seen.add(p)
                out.append(s.pt[p])
    return np.array(out)

GOLD = (0.949, 0.761, 0.18)
G = cloud(groups[GOLD])

print("=== gold: any material below z=0.05 outside y[-5.300,-4.450]? ===")
low = G[G[:, 2] < 0.05]
print(f"  gold pts z<0.05: {len(low)}  y range [{low[:,1].min():.3f},{low[:,1].max():.3f}]")
outside = low[(low[:, 1] > -4.4499) | (low[:, 1] < -5.3001)]
print(f"  of those, outside the foot y-band: {len(outside)}")
if len(outside):
    for p in outside[:20]:
        print(f"    ({p[0]:+.3f},{p[1]:+.3f},{p[2]:+.3f})")

print("\n=== gold z-vs-y profile (min z of gold in each 0.25mm y bin) ===")
for y0 in np.arange(-5.5, -2.0, 0.25):
    sel = G[(G[:, 1] >= y0) & (G[:, 1] < y0 + 0.25)]
    if len(sel):
        print(f"  y [{y0:+.2f},{y0+0.25:+.2f})  n={len(sel):4d}  "
              f"z min {sel[:,2].min():+.3f}  max {sel[:,2].max():+.3f}")

print("\n=== other colour groups: Y extent at low z (body / shell rear face) ===")
for key, roots in sorted(groups.items(), key=lambda t: -len(t[1])):
    C = cloud(roots)
    if not len(C):
        continue
    print(f"\n colour {key}  n_pts={len(C)}  "
          f"X[{C[:,0].min():+.3f},{C[:,0].max():+.3f}] "
          f"Y[{C[:,1].min():+.3f},{C[:,1].max():+.3f}] "
          f"Z[{C[:,2].min():+.3f},{C[:,2].max():+.3f}]")
    # rear-most (most negative Y) material, and where it sits in z
    ymin = C[:, 1].min()
    rear = C[np.abs(C[:, 1] - ymin) < 0.01]
    print(f"   rear-most face y={ymin:+.3f}  z[{rear[:,2].min():+.3f},{rear[:,2].max():+.3f}]"
          f"  x[{rear[:,0].min():+.3f},{rear[:,0].max():+.3f}]")
    # what is the rear-most material that is LOW (z<0.6), i.e. could block a fillet
    lo = C[C[:, 2] < 0.6]
    if len(lo):
        print(f"   low material (z<0.6): y[{lo[:,1].min():+.3f},{lo[:,1].max():+.3f}]"
              f"  x[{lo[:,0].min():+.3f},{lo[:,0].max():+.3f}]")

print("\n=== overhang over the foot band: any non-gold material at y in "
      "[-5.35,-4.35] and z < 1.0 ? ===")
for key, roots in groups.items():
    if key == GOLD:
        continue
    C = cloud(roots)
    sel = C[(C[:, 1] > -5.35) & (C[:, 1] < -4.35) & (C[:, 2] < 1.0)]
    if len(sel):
        print(f"  colour {key}: n={len(sel)}  y[{sel[:,1].min():+.3f},{sel[:,1].max():+.3f}]"
              f"  z[{sel[:,2].min():+.3f},{sel[:,2].max():+.3f}]"
              f"  x[{sel[:,0].min():+.3f},{sel[:,0].max():+.3f}]")
