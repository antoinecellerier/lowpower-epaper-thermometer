#!/usr/bin/env python3
"""Analyse the RECOMMEND P.C.B LAYOUT view of the HRO datasheet, from exact
vector geometry (page content stream, CTM composed).

Drawing frame (the orientation you read the sheet in):
    DX = -y_pdf   (increases to the RIGHT)
    DY = -x_pdf   (increases DOWNWARD)
so a "horizontal line on the sheet" is a constant-DY run.
"""
import json
import sys
from collections import defaultdict

V = json.load(open("archive/proofs/j3-datum/vector.json"))
SEGS = V["segs"]


def to_draw(x, y):
    return (-y, -x)


def load(region=None):
    """region = (dx0, dx1, dy0, dy1) in drawing pts."""
    out = []
    for x0, y0, x1, y1, pid, layer in SEGS:
        a = to_draw(x0, y0)
        b = to_draw(x1, y1)
        if region:
            dx0, dx1, dy0, dy1 = region
            mx = (a[0] + b[0]) / 2
            my = (a[1] + b[1]) / 2
            if not (dx0 <= mx <= dx1 and dy0 <= my <= dy1):
                continue
        out.append((a[0], a[1], b[0], b[1], pid, layer))
    return out


# layout view region, in drawing pts (derived from the 150dpi overview)
# img_x = (842 + DX)*s ; img_y = (595 + DY)*s   with s = dpi/72
def img_to_draw(ix, iy, dpi=150):
    s = dpi / 72.0
    return (ix / s - 842.0, iy / s - 595.0)


REGION = (*img_to_draw(640, 40)[0:1], img_to_draw(1120, 40)[0],
          img_to_draw(640, 40)[1], img_to_draw(640, 450)[1])
REGION = (img_to_draw(640, 40)[0], img_to_draw(1120, 40)[0],
          img_to_draw(640, 40)[1], img_to_draw(640, 460)[1])

if __name__ == "__main__":
    segs = load(REGION)
    print(f"region DX[{REGION[0]:.1f},{REGION[1]:.1f}] DY[{REGION[2]:.1f},{REGION[3]:.1f}]")
    print(f"segments in region: {len(segs)}")

    EPS = 0.05
    horiz = defaultdict(list)   # DY -> list of (dx0,dx1)
    vert = defaultdict(list)    # DX -> list of (dy0,dy1)
    other = 0
    for ax, ay, bx, by, pid, layer in segs:
        if abs(ay - by) < EPS and abs(ax - bx) > EPS:
            horiz[round((ay + by) / 2, 2)].append((min(ax, bx), max(ax, bx)))
        elif abs(ax - bx) < EPS and abs(ay - by) > EPS:
            vert[round((ax + bx) / 2, 2)].append((min(ay, by), max(ay, by)))
        else:
            other += 1
    print(f"horiz levels {len(horiz)}  vert levels {len(vert)}  diag/other {other}")

    def merge(runs):
        runs = sorted(runs)
        out = []
        for a, b in runs:
            if out and a <= out[-1][1] + 0.6:
                out[-1][1] = max(out[-1][1], b)
            else:
                out.append([a, b])
        return out

    print("\n=== long horizontal lines (>=12pt) ===")
    for dy in sorted(horiz):
        for a, b in merge(horiz[dy]):
            if b - a >= 12:
                print(f"  DY={dy:9.3f}  DX {a:9.3f} .. {b:9.3f}  len={b-a:7.3f}")
    print("\n=== long vertical lines (>=12pt) ===")
    for dx in sorted(vert):
        for a, b in merge(vert[dx]):
            if b - a >= 12:
                print(f"  DX={dx:9.3f}  DY {a:9.3f} .. {b:9.3f}  len={b-a:7.3f}")
