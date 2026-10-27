#!/usr/bin/env python3
"""Locate the arrow-tip terminations of the vertical dimensions (0.50, 1.64,
4.18, 5.79) in the RECOMMEND P.C.B LAYOUT view, and the exact extents of the
pads / slots / NPTH circles / PCB EDGE line.

Arrowheads are filled triangles; their TIP is the vertex farthest from the
triangle's base.  We find every closed 3-vertex path near a dimension column
and report its tip.
"""
import json
from collections import defaultdict

V = json.load(open("archive/proofs/j3-datum/vector.json"))
PT_PER_MM = 12.24
PCB_EDGE = -431.720


def paths(dx0, dx1, dy0, dy1):
    P = defaultdict(list)
    for x0, y0, x1, y1, pid, layer in V["segs"]:
        a = (-y0, -x0)
        b = (-y1, -x1)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if dx0 <= mx <= dx1 and dy0 <= my <= dy1:
            P[pid].append((a, b))
    return P


def tri_tip(sl):
    """If the path's vertices form a triangle, return (tip, base_mid, size)."""
    vs = []
    for a, b in sl:
        for p in (a, b):
            if not any(abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6 for q in vs):
                vs.append(p)
    if len(vs) != 3:
        return None
    # tip = vertex opposite the longest... no: opposite the SHORTEST side is
    # wrong for slim arrows.  Arrow base is the short edge (width), tip is the
    # vertex not on it.  Find the pair of vertices closest together = base.
    import itertools
    best = None
    for i, j in itertools.combinations(range(3), 2):
        d = (vs[i][0] - vs[j][0]) ** 2 + (vs[i][1] - vs[j][1]) ** 2
        if best is None or d < best[0]:
            best = (d, i, j)
    _, i, j = best
    k = 3 - i - j
    base_mid = ((vs[i][0] + vs[j][0]) / 2, (vs[i][1] + vs[j][1]) / 2)
    w = best[0] ** 0.5
    L = ((vs[k][0] - base_mid[0]) ** 2 + (vs[k][1] - base_mid[1]) ** 2) ** 0.5
    return vs[k], base_mid, w, L


def column(label, dxc, half=4.0, dy0=-600, dy1=-360):
    print(f"\n=== {label}: vertical dimension column DX ~ {dxc} ===")
    P = paths(dxc - half, dxc + half, dy0, dy1)
    tips = []
    for pid, sl in P.items():
        t = tri_tip(sl)
        if t and 1.0 < t[3] < 8.0 and 0.5 < t[2] < 4.0:
            tip, bm, w, L = t
            tips.append((tip[1], tip[0], bm[1], w, L, pid))
    tips.sort()
    for ty, tx, bmy, w, L, pid in tips:
        print(f"  ARROW tip DY={ty:9.3f} DX={tx:8.3f}  base_mid_DY={bmy:9.3f} "
              f"w={w:5.2f} L={L:5.2f} pid={pid}  "
              f"[{(ty - PCB_EDGE) / PT_PER_MM:+7.4f} mm from PCB EDGE]")
    if len(tips) >= 2:
        span = tips[-1][0] - tips[0][0]
        print(f"  --> outermost tip span = {span:.3f} pt = {span / PT_PER_MM:.4f} mm")
    return tips


if __name__ == "__main__":
    for lab, dxc in [("5.79", -331.040), ("4.18", -339.680),
                     ("1.64", -352.640), ("0.50", -361.0)]:
        column(lab, dxc)
