#!/usr/bin/env python3
"""HRO drawing: the 12 pad rectangles' X positions and widths, plus the four
oval slots and two round holes, re-extracted from archive/proofs/j3-datum/vector.json.

Needed here because the land comparison has to cover the X (side) axis too,
which the j3-datum verdict only treated in Y.  Same connected-component method
as archive/proofs/j3-datum/objects.py; the X datum is the layout view's mirror centreline,
computed from the objects themselves (not assumed).
"""
import sys, os, json
sys.path.insert(0, "archive/proofs/j3-datum")
from objects import segs, components, bbox, PT_PER_MM, PCB_EDGE

S = segs()
C = components(S)
rows = []
for sl in C:
    x0, y0, x1, y1 = bbox(sl)
    w, h = (x1 - x0) / PT_PER_MM, (y1 - y0) / PT_PER_MM
    if w < 0.05 or h < 0.05:
        continue
    rows.append(dict(dx0=x0, dx1=x1, w=w, h=h,
                     top=(PCB_EDGE - y0) / PT_PER_MM,
                     bot=(PCB_EDGE - y1) / PT_PER_MM, n=len(sl)))

# pads: height ~1.137, tops ~7.41
pads = [r for r in rows if 1.0 < r["h"] < 1.30 and 7.2 < r["top"] < 7.6]
pads.sort(key=lambda r: r["dx0"])
print(f"pad rectangles found: {len(pads)}")

# X datum = mirror centreline of the pad set
ctrs = [(p["dx0"] + p["dx1"]) / 2 for p in pads]
XC = (min(ctrs) + max(ctrs)) / 2
print(f"X datum (pad-set mirror centreline) = {XC:.3f} pt")

print(f"\n{'#':>3} {'x_ctr_mm':>10} {'width_mm':>9} {'y_near':>8} {'y_far':>8} {'h_mm':>7}")
out = []
for i, p in enumerate(pads):
    xc = ((p["dx0"] + p["dx1"]) / 2 - XC) / PT_PER_MM
    out.append(dict(xc=xc, w=p["w"], near=p["bot"], far=p["top"]))
    print(f"{i:3d} {xc:10.4f} {p['w']:9.4f} {p['bot']:8.4f} {p['top']:8.4f} {p['h']:7.4f}")

print("\nother large objects (slots / holes / edge):")
for r in sorted(rows, key=lambda q: q["top"]):
    if r in pads:
        continue
    xc = ((r["dx0"] + r["dx1"]) / 2 - XC) / PT_PER_MM
    print(f"  x_ctr {xc:+8.4f}  w {r['w']:7.4f}  h {r['h']:7.4f}  "
          f"y_near {r['bot']:8.4f}  y_far {r['top']:8.4f}  n={r['n']}")

json.dump(dict(XC_pt=XC, pads=out),
          open("archive/proofs/j3-land/drawing_pads.json", "w"), indent=1)
