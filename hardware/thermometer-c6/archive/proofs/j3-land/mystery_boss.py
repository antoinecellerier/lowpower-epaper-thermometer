#!/usr/bin/env python3
"""What is the below-board material at (|x| ~3.10-3.25, y ~ -4.55..-4.70)?

Our footprint has no hole there, so if it is a real solid boss it is a
collision and a separate finding.  Enumerate every face owning a vertex in
that window and report its full extent -- a real boss has faces spanning a
range of z; a SolidWorks export artifact lives only on the z=-0.851 plane.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from step_parse import Step

s = Step()
faces = [i for i, k in s.kind.items() if k == "ADVANCED_FACE"]
print(f"ADVANCED_FACEs: {len(faces)}")

hits = []
for f in faces:
    info = s.face_info(f)
    v = info["verts"]
    if not len(v):
        continue
    sel = (np.abs(v[:, 0]) > 3.0) & (np.abs(v[:, 0]) < 3.4) & \
          (v[:, 1] > -4.75) & (v[:, 1] < -4.45) & (v[:, 2] < -0.2)
    if sel.any():
        hits.append(info)

print(f"faces with a vertex in the window: {len(hits)}\n")
for info in hits:
    v = info["verts"]
    n = info["normal"]
    ntxt = "-" if n is None else f"({n[0]:+.2f},{n[1]:+.2f},{n[2]:+.2f})"
    print(f"  #{info['id']:6d} {info['surf']:>22} n={ntxt:>20} "
          f"x[{v[:,0].min():+.3f},{v[:,0].max():+.3f}] "
          f"y[{v[:,1].min():+.3f},{v[:,1].max():+.3f}] "
          f"z[{v[:,2].min():+.3f},{v[:,2].max():+.3f}]  nv={len(v)}")
    for p in sorted(v.tolist(), key=lambda q: (q[2], q[1], q[0]))[:12]:
        print(f"        ({p[0]:+.4f},{p[1]:+.4f},{p[2]:+.4f})")

print("\n=== how much material is there at each z plane in that window? ===")
P = np.array(list(s.pt.values()))
w = P[(np.abs(P[:, 0]) > 2.9) & (np.abs(P[:, 0]) < 3.5)
      & (P[:, 1] > -4.80) & (P[:, 1] < -4.40)]
print(f"points in window (all z): {len(w)}")
for z in sorted({round(float(t), 4) for t in w[:, 2]}):
    sel = w[np.abs(w[:, 2] - z) < 1e-4]
    print(f"  z={z:+.4f} n={len(sel)}  x[{sel[:,0].min():+.3f},{sel[:,0].max():+.3f}]"
          f" y[{sel[:,1].min():+.3f},{sel[:,1].max():+.3f}]")

print("\n=== the two r=0.15 cylinders: do they have vertices off the z=-0.851 plane? ===")
for cid in (10944, 26059, 27831):
    if cid not in s.ent:
        continue
    owners = [f for f in faces if s.refs[f] and s.refs[f][-1] == cid]
    print(f"  cylinder #{cid}: {s.ent[cid].strip()[:90]}")
    print(f"    owning faces: {owners}")
    for f in owners:
        v = s.face_info(f)["verts"]
        if len(v):
            print(f"      face #{f}: z[{v[:,2].min():+.4f},{v[:,2].max():+.4f}] "
                  f"x[{v[:,0].min():+.3f},{v[:,0].max():+.3f}] "
                  f"y[{v[:,1].min():+.3f},{v[:,1].max():+.3f}]")
