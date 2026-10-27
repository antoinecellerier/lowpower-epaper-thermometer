#!/usr/bin/env python3
"""Exact object extents in the RECOMMEND P.C.B LAYOUT view: the 12 pad
rectangles, the 4 oval slots, the 2 round holes, the PCB EDGE line.

Objects are recovered by connected-component clustering of the outline
segments (the drawing has no closed-entity structure), restricted to the
"0" / geometry layers and excluding hatch (hatch lines are 45-degree).
"""
import json
from collections import defaultdict

V = json.load(open("archive/proofs/j3-datum/vector.json"))
PT_PER_MM = 12.24
PCB_EDGE = -431.720

DX0, DX1 = -536.0, -370.0     # the drawing body only (no dimension columns)
DY0, DY1 = -540.0, -420.0


def segs():
    out = []
    for x0, y0, x1, y1, pid, layer in V["segs"]:
        a = (-y0, -x0)
        b = (-y1, -x1)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if DX0 <= mx <= DX1 and DY0 <= my <= DY1:
            out.append((a, b))
    return out


def components(S, tol=0.35):
    """Union-find on shared endpoints."""
    par = list(range(len(S)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    def uni(i, j):
        a, b = find(i), find(j)
        if a != b:
            par[a] = b

    grid = defaultdict(list)
    q = tol * 2

    def key(p):
        return (round(p[0] / q), round(p[1] / q))

    for i, (a, b) in enumerate(S):
        for p in (a, b):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    grid[(key(p)[0] + dx, key(p)[1] + dy)].append((i, p))
    seen = set()
    for cell, items in grid.items():
        for x in range(len(items)):
            for y in range(x + 1, len(items)):
                i, p = items[x]
                j, r = items[y]
                if i == j:
                    continue
                if abs(p[0] - r[0]) < tol and abs(p[1] - r[1]) < tol:
                    uni(i, j)
    comp = defaultdict(list)
    for i in range(len(S)):
        comp[find(i)].append(S[i])
    return list(comp.values())


def bbox(sl):
    xs = [p for a, b in sl for p in (a[0], b[0])]
    ys = [p for a, b in sl for p in (a[1], b[1])]
    return min(xs), min(ys), max(xs), max(ys)


if __name__ == "__main__":
    S = segs()
    C = components(S)
    rows = []
    for sl in C:
        x0, y0, x1, y1 = bbox(sl)
        w, h = x1 - x0, y1 - y0
        if w < 1.0 and h < 1.0:
            continue
        rows.append((x0, y0, x1, y1, w, h, len(sl)))
    rows.sort(key=lambda r: (round(r[1], 1), r[0]))
    print(f"{len(rows)} objects (DX0 DY0 DX1 DY1 in pt; sizes in mm; "
          f"DY in mm above PCB EDGE)")
    print(f"{'DX0':>9} {'DX1':>9} {'DY0':>9} {'DY1':>9} | {'w_mm':>7} {'h_mm':>7} |"
          f" {'top_mm':>8} {'bot_mm':>8} {'ctr_mm':>8} | n")
    for x0, y0, x1, y1, w, h, n in rows:
        print(f"{x0:9.2f} {x1:9.2f} {y0:9.2f} {y1:9.2f} | "
              f"{w/PT_PER_MM:7.4f} {h/PT_PER_MM:7.4f} | "
              f"{(PCB_EDGE-y0)/PT_PER_MM:8.4f} {(PCB_EDGE-y1)/PT_PER_MM:8.4f} "
              f"{(PCB_EDGE-(y0+y1)/2)/PT_PER_MM:8.4f} | {n}")
