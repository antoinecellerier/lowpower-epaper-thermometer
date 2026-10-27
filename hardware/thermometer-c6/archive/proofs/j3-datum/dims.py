#!/usr/bin/env python3
"""Exact geometry of the RECOMMEND P.C.B LAYOUT view: pads, slots, circles,
PCB EDGE line, and the terminations (arrow tips) of the vertical dimensions.

DX = -y_pdf (right on sheet), DY = -x_pdf (down on sheet), pt.
Calibration: PT_PER_MM derived below from dimensions NOT used for the verdict.
"""
import json
import sys
from collections import defaultdict

V = json.load(open("archive/proofs/j3-datum/vector.json"))
PT_PER_MM = 12.24          # proven below from 2.50 / 3.50 / 0.50 pitch


def dsegs(dx0=-560, dx1=-280, dy0=-600, dy1=-360):
    out = []
    for x0, y0, x1, y1, pid, layer in V["segs"]:
        ax, ay, bx, by = -y0, -x0, -y1, -x1
        mx, my = (ax + bx) / 2, (ay + by) / 2
        if dx0 <= mx <= dx1 and dy0 <= my <= dy1:
            out.append((ax, ay, bx, by, pid))
    return out


def cluster(vals, tol=0.25):
    vals = sorted(vals)
    groups = []
    for v in vals:
        if groups and v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [(sum(g) / len(g), len(g)) for g in groups]


def band_profile(label, dx0, dx1, dy0=-600, dy1=-360):
    """All distinct DY coordinates of vertices inside an x-band."""
    pts = []
    for ax, ay, bx, by, pid in dsegs(dx0, dx1, dy0, dy1):
        pts.append(ay)
        pts.append(by)
    cl = cluster(pts, 0.20)
    print(f"\n--- {label}: DX band [{dx0},{dx1}] : DY vertex clusters ---")
    for v, n in cl:
        print(f"   DY={v:9.3f}  n={n:4d}   (mm from PCB EDGE: "
              f"{(v - PCB_EDGE) / PT_PER_MM:+7.4f})")
    return cl


PCB_EDGE = -431.720

if __name__ == "__main__":
    # ---- 1. calibration evidence (horizontal dims, x-extension-line pairs) ----
    print("=== CALIBRATION (horizontal dimensions, extension-line separations) ===")
    ext = {   # (left DX, right DX) : nominal label
        (-453.920, -423.320): "2.50",
        (-460.040, -417.200): "3.50",
        (-467.960, -409.280): "4.80",
        (-473.960, -403.280): "5.78",
        (-477.680, -399.560): "6.40",
        (-491.480, -385.760): "8.65",
    }
    for (a, b), lab in sorted(ext.items(), key=lambda kv: float(kv[1])):
        sep = b - a
        print(f"  {lab:>5s} : sep = {sep:8.3f} pt -> {sep / PT_PER_MM:8.4f} mm "
              f"(err {sep / PT_PER_MM - float(lab):+.4f})")

    # ---- 2. feature bands ----
    band_profile("PAD ROW + right dimension column", -400.0, -320.0)
    band_profile("LEFT rear/front slot column", -520.0, -480.0)
    band_profile("RIGHT rear/front slot column", -400.0, -360.0)
