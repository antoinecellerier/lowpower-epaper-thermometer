#!/usr/bin/env python3
"""Merged horizontal / vertical line runs inside the RECOMMEND P.C.B LAYOUT view.

Drawing frame: DX = -y_pdf (right), DY = -x_pdf (down), units = PDF pt.
"""
import json
import sys
from collections import defaultdict

V = json.load(open("archive/proofs/j3-datum/vector.json"))

DX0, DX1 = -536.0, -296.0
DY0, DY1 = -580.0, -368.0
EPS = 0.03


def runs(minlen=3.0):
    horiz, vert = defaultdict(list), defaultdict(list)
    for x0, y0, x1, y1, pid, layer in V["segs"]:
        ax, ay, bx, by = -y0, -x0, -y1, -x1
        mx, my = (ax + bx) / 2, (ay + by) / 2
        if not (DX0 <= mx <= DX1 and DY0 <= my <= DY1):
            continue
        if abs(ay - by) < EPS and abs(ax - bx) > EPS:
            horiz[round((ay + by) / 2, 2)].append((min(ax, bx), max(ax, bx)))
        elif abs(ax - bx) < EPS and abs(ay - by) > EPS:
            vert[round((ax + bx) / 2, 2)].append((min(ay, by), max(ay, by)))

    def merge(rs, gap=1.0):
        rs = sorted(rs)
        out = []
        for a, b in rs:
            if out and a <= out[-1][1] + gap:
                out[-1][1] = max(out[-1][1], b)
            else:
                out.append([a, b])
        return [r for r in out if r[1] - r[0] >= minlen]
    H = {k: merge(v) for k, v in horiz.items()}
    Vt = {k: merge(v) for k, v in vert.items()}
    return {k: v for k, v in H.items() if v}, {k: v for k, v in Vt.items() if v}


if __name__ == "__main__":
    minlen = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    H, Vt = runs(minlen)
    print(f"=== horizontal runs (len >= {minlen}pt) : level DY, extent DX ===")
    for dy in sorted(H):
        for a, b in H[dy]:
            print(f"  DY={dy:9.3f} (AU {dy/0.12:9.1f})  DX {a:9.3f}..{b:9.3f}  len={b-a:8.3f}")
    print(f"\n=== vertical runs (len >= {minlen}pt) : column DX, extent DY ===")
    for dx in sorted(Vt):
        for a, b in Vt[dx]:
            print(f"  DX={dx:9.3f} (AU {dx/0.12:9.1f})  DY {a:9.3f}..{b:9.3f}  len={b-a:8.3f}")
