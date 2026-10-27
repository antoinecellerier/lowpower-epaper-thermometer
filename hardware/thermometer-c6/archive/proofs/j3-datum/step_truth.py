#!/usr/bin/env python3
"""Manufacturer ground truth for the PART, straight out of the JLC/EasyEDA STEP.

Independent of the datasheet drawing.  Extracts, in the model's own frame:
  * the 4 shell through-hole leg (peg) axes  -> front/rear leg rows
  * the 2 plastic NPTH post axes
  * the gold SMT tail feet row (z ~ 0)
  * the shell mouth / front face plane and the rear-most body plane
and reports the part's depth chain, to be compared with the drawing.

Method: pure CARTESIAN_POINT cloud, sliced by z, plus colour isolation for
gold.  No CAD kernel needed.
"""
import re
import numpy as np

STEP = "local.3dmodels/USB_C_Receptacle_HRO_TYPE-C-31-M-12.step"


def load():
    data = open(STEP, encoding="latin-1").read()
    pts = []
    for m in re.finditer(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(([^)]*)\)\s*\)", data):
        n = re.findall(r"[-+0-9.Ee]+", m.group(1))
        if len(n) == 3:
            pts.append([float(x) for x in n])
    return np.array(pts), data


def clusters(v, tol=0.15):
    v = np.sort(v)
    out, cur = [], [v[0]]
    for x in v[1:]:
        if x - cur[-1] <= tol:
            cur.append(x)
        else:
            out.append(cur)
            cur = [x]
    out.append(cur)
    return [(float(np.mean(c)), float(min(c)), float(max(c)), len(c)) for c in out]


P, data = load()
print(f"points: {len(P)}")
print(f"raw bbox  X[{P[:,0].min():.3f},{P[:,0].max():.3f}]"
      f"  Y[{P[:,1].min():.3f},{P[:,1].max():.3f}]"
      f"  Z[{P[:,2].min():.3f},{P[:,2].max():.3f}]")

# ---------------------------------------------------------------- below-board
# Everything with z < -0.15 is the part of the pegs/posts that enters the PCB.
sub = P[P[:, 2] < -0.15]
print(f"\nbelow-board points (z<-0.15): {len(sub)}   "
      f"z range [{sub[:,2].min():.3f},{sub[:,2].max():.3f}]")
print("  their Y clusters (peg/post rows):")
for mean, lo, hi, n in clusters(sub[:, 1], 0.30):
    sel = sub[np.abs(sub[:, 1] - mean) < 0.9]
    print(f"    Y ~ {mean:+8.3f}  [{lo:+7.3f},{hi:+7.3f}]  n={n:5d}  "
          f"X extent [{sel[:,0].min():+7.3f},{sel[:,0].max():+7.3f}]")

# separate by |X|: shell legs are the outer pair, plastic posts the inner
print("\n  split by |X| (legs = outer, posts = inner):")
for lab, lo_x, hi_x in (("shell leg", 3.6, 5.2), ("NPTH post", 2.3, 3.4)):
    s = sub[(np.abs(sub[:, 0]) >= lo_x) & (np.abs(sub[:, 0]) <= hi_x)]
    if not len(s):
        continue
    print(f"    {lab}: n={len(s)}  |X| ctr "
          f"{np.mean(np.abs(s[:,0])):.3f}")
    for mean, lo, hi, n in clusters(s[:, 1], 0.35):
        print(f"       Y row {mean:+8.3f}  span[{lo:+7.3f},{hi:+7.3f}] n={n}")

# ------------------------------------------------------------------ mouth/body
# The metal shell at plug height.  Take a z slice through the shell walls and
# look at the Y extremes of the wide (|X| > 3.5) material.
for zlo, zhi in ((1.2, 2.4), (0.3, 3.0)):
    s = P[(P[:, 2] > zlo) & (P[:, 2] < zhi)]
    s = s[np.abs(s[:, 0]) < 5.0]
    print(f"\nshell slice z[{zlo},{zhi}]: n={len(s)}  "
          f"X[{s[:,0].min():+.3f},{s[:,0].max():+.3f}]  "
          f"Y[{s[:,1].min():+.3f},{s[:,1].max():+.3f}]")
    print("   Y clusters:", [f"{m:+.3f}(n={n})" for m, _, _, n in clusters(s[:, 1], 0.25)][:14])

# widest cross-section = the 8.94 body width; find where it lives in Y
wide = P[np.abs(np.abs(P[:, 0]) - 4.47) < 0.06]
if len(wide):
    print(f"\npoints at |X| ~ 4.47 (the 8.94 body width): n={len(wide)}  "
          f"Y[{wide[:,1].min():+.3f},{wide[:,1].max():+.3f}]  "
          f"Z[{wide[:,2].min():+.3f},{wide[:,2].max():+.3f}]")
