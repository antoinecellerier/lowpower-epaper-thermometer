#!/usr/bin/env python3
"""Measure the 16 SMT solder feet of HRO TYPE-C-31-M-12 from the STEP model.

Isolation method (all three conditions must hold, none assumed):
  1. the face is gold-coloured (STYLED_ITEM -> COLOUR_RGB 0.949/0.761/0.180),
     i.e. a contact, not the shell / plastic;
  2. its surface is a PLANE whose normal is parallel to Z (|n.z| > 0.999),
     i.e. a flat horizontal face, not the bent riser or a fillet;
  3. its plane origin sits at z = 0 within ZTOL, i.e. it is the *board-
     contacting* face and not the 0.20 mm-up top face of the same tail.

Only then is the face's outline measured. The result is a true face outline
(from its own VERTEX_POINTs and any arc geometry), not a z-slice of a point
cloud, so nothing is inferred about where the flat part "probably" ends.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from step_parse import Step

ZTOL = 1e-4      # the model is exact: gold z values quantise to 0.0000 / 0.2000
NTOL = 1e-3


def is_gold(rgb):
    if not rgb:
        return False
    r, g, b = rgb
    return r > 0.6 and g > 0.4 and b < 0.4 and r > b + 0.4


def main():
    s = Step()
    gold_faces = [geo for _, rgb, geo in s.styled_items()
                  if is_gold(rgb) and s.kind.get(geo) == "ADVANCED_FACE"]
    print(f"gold ADVANCED_FACEs: {len(gold_faces)}")

    infos = [s.face_info(f) for f in gold_faces]
    by_surf = {}
    for i in infos:
        by_surf[i["surf"]] = by_surf.get(i["surf"], 0) + 1
    print("  by surface type:", by_surf)

    planar_z = [i for i in infos
                if i["surf"] == "PLANE" and i["normal"] is not None
                and abs(abs(i["normal"][2]) - 1.0) < NTOL]
    print(f"  planar + Z-normal: {len(planar_z)}")
    zs = sorted({round(float(i["origin"][2]), 4) for i in planar_z})
    print("  their plane-origin z values:", zs)

    bottom = [i for i in planar_z if abs(i["origin"][2]) < ZTOL]
    print(f"  at z=0 (board plane): {len(bottom)} faces")

    # cluster the bottom faces by x
    rows = []
    for i in bottom:
        v = i["verts"]
        rows.append(dict(id=i["id"], x0=float(v[:, 0].min()), x1=float(v[:, 0].max()),
                         y0=float(v[:, 1].min()), y1=float(v[:, 1].max()),
                         n=len(v)))
    rows.sort(key=lambda r: (r["x0"] + r["x1"]) / 2)
    print(f"\n{'#':>3} {'xc':>8} {'width':>7} {'y_lo':>8} {'y_hi':>8} {'len':>6} {'nv':>3}")
    for k, r in enumerate(rows):
        print(f"{k:3d} {(r['x0']+r['x1'])/2:8.3f} {r['x1']-r['x0']:7.3f} "
              f"{r['y0']:8.3f} {r['y1']:8.3f} {r['y1']-r['y0']:6.3f} {r['n']:3d}")

    json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "feet.json"), "w"), indent=1)

    # also dump the full vertex list of one representative foot
    if rows:
        rep = max(rows, key=lambda r: r["x1"] - r["x0"])
        info = next(i for i in bottom if i["id"] == rep["id"])
        print(f"\nrepresentative wide foot face #{rep['id']} vertices:")
        for v in sorted(info["verts"].tolist(), key=lambda p: (p[1], p[0])):
            print(f"   ({v[0]:+.4f}, {v[1]:+.4f}, {v[2]:+.4f})")


if __name__ == "__main__":
    main()
