#!/usr/bin/env python3
"""Feature extraction for the RECOMMEND P.C.B LAYOUT view (exact vectors).

Drawing frame:  DX = -y_pdf (right), DY = -x_pdf (down).  Units: PDF points.
All source coords are integer AutoCAD units x 0.12, so we report in AU too
(AU = pt / 0.12) to make exactness visible.
"""
import json
from collections import defaultdict

V = json.load(open("archive/proofs/j3-datum/vector.json"))

# layout view bounds in drawing pts (generous)
DX0, DX1 = -536.0, -300.0
DY0, DY1 = -580.0, -370.0


def draw_segs():
    out = defaultdict(list)     # pathid -> [(ax,ay,bx,by)]
    for x0, y0, x1, y1, pid, layer in V["segs"]:
        a = (-y0, -x0)
        b = (-y1, -x1)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if DX0 <= mx <= DX1 and DY0 <= my <= DY1:
            out[pid].append((a[0], a[1], b[0], b[1]))
    return out


def bbox(sl):
    xs = [p for s in sl for p in (s[0], s[2])]
    ys = [p for s in sl for p in (s[1], s[3])]
    return min(xs), min(ys), max(xs), max(ys)


if __name__ == "__main__":
    P = draw_segs()
    print(f"paths in region: {len(P)}")
    rows = []
    for pid, sl in P.items():
        x0, y0, x1, y1 = bbox(sl)
        rows.append((len(sl), x0, y0, x1, y1, pid))
    # big paths first
    rows.sort(key=lambda r: -( (r[3]-r[1]) * (r[4]-r[2]) ))
    print("\n=== 40 largest-area paths (DX0,DY0,DX1,DY1 in pt) ===")
    for n, x0, y0, x1, y1, pid in rows[:40]:
        print(f" pid={pid:6d} nseg={n:4d}  DX[{x0:9.2f},{x1:9.2f}] w={x1-x0:7.2f}"
              f"  DY[{y0:9.2f},{y1:9.2f}] h={y1-y0:7.2f}")
