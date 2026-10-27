#!/usr/bin/env python3
"""Validate the X datum used by drawing_pads.py.

drawing_pads.py takes the X origin from the pad set's own mirror centreline.
If that is right, the mechanical features -- which were NOT used to build it --
must land on their nominal pitches: NPTH posts at +-2.890 (drawn 5.78) and the
oval shell slots at +-4.320 (drawn 8.65/8.64).  This script lists every object
in the layout view against that datum so the check is visible, not asserted.
"""
import sys
sys.path.insert(0, "archive/proofs/j3-datum")
from objects import segs, components, bbox, PT_PER_MM, PCB_EDGE

XC = -438.620          # from drawing_pads.py (pad-set mirror centreline)

S = segs()
C = components(S)
rows = []
for sl in C:
    x0, y0, x1, y1 = bbox(sl)
    w, h = (x1 - x0) / PT_PER_MM, (y1 - y0) / PT_PER_MM
    if w < 0.15 or h < 0.15:
        continue
    top, bot = (PCB_EDGE - y0) / PT_PER_MM, (PCB_EDGE - y1) / PT_PER_MM
    if not (-0.5 < bot < 8.0):
        continue
    rows.append(((x0 + x1) / 2 - XC, w, h, bot, top, len(sl)))

rows.sort(key=lambda r: (-(r[1] * r[2]), r[0]))
print(f"{'x_ctr_mm':>10} {'w_mm':>8} {'h_mm':>8} {'y_near':>8} {'y_far':>8} "
      f"{'y_ctr':>8}  n")
for xc, w, h, bot, top, n in rows:
    print(f"{xc/PT_PER_MM:10.4f} {w:8.4f} {h:8.4f} {bot:8.4f} {top:8.4f} "
          f"{(bot+top)/2:8.4f}  {n}")
