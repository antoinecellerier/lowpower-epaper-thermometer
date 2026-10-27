#!/usr/bin/env python3
"""Method 2: independent high-DPI raster measurement of the layout view.

Page 1 rendered at 1200 dpi.  Features are located by pixel scanning inside
coarse windows and measured in mm with the SAME scale constant (204 px/mm =
12.24 pt/mm at 1200dpi).  Vector coordinates are used only to pick the coarse
windows; every reported number comes from the pixels.
"""
import os
import subprocess
import numpy as np
from PIL import Image

PDF = "datasheets/HRO_TYPE-C-31-M-12_datasheet.pdf"
DPI = 1200
CX, CY, CW, CH = 5200, 400, 3800, 3300
OUT = "out/j3-datum/rc"                # raster scratch, read by make_images.py
PX_PER_MM = 12.24 * DPI / 72.0        # 204.000 px/mm


def render():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-x", str(CX), "-y",
                    str(CY), "-W", str(CW), "-H", str(CH), PDF, OUT],
                   check=True, capture_output=True)
    return np.array(Image.open(OUT + "-1.png").convert("L")) < 128


A = render()
H, W = A.shape
print(f"raster {W}x{H} @ {DPI}dpi, {PX_PER_MM:.1f} px/mm")

# ---- 1. PCB EDGE: longest horizontal dark run in the lower half -------------
best = None
for y in range(1500, 2800):
    n = int(A[y].sum())
    if best is None or n > best[0]:
        best = (n, y)
# refine: the line is ~2px thick, take the intensity-weighted centre
n, y0 = best
ys = [y for y in range(y0 - 4, y0 + 5) if A[y].sum() > 0.5 * n]
EDGE = float(np.average(ys, weights=[A[y].sum() for y in ys]))
print(f"PCB EDGE line: rows {ys}  (darkest row {y0}, {n} dark px) -> {EDGE:.2f}")


def mm(y):
    return (EDGE - y) / PX_PER_MM


def vspan(x0, x1, y0, y1, frac=0.5):
    """First and last row in [y0,y1) where >= frac of the x-band is dark."""
    band = A[y0:y1, x0:x1].mean(axis=1)
    ys = np.where(band >= frac)[0]
    if not len(ys):
        return None
    return y0 + ys[0], y0 + ys[-1] + 1


def edges(x0, x1, y0, y1, frac=0.5):
    """Contiguous dark groups."""
    band = A[y0:y1, x0:x1].mean(axis=1)
    ys = np.where(band >= frac)[0]
    out, s = [], None
    for i, v in enumerate(ys):
        if s is None:
            s = v
        elif v - ys[i - 1] > 3:
            out.append((y0 + s, y0 + ys[i - 1] + 1))
            s = v
    if s is not None:
        out.append((y0 + s, y0 + ys[-1] + 1))
    return out


print("\n=== features, mm above the PCB EDGE line (raster) ===")

# ---- 2. pad row: hatched interior of a wide pad and of narrow pads ----------
for lab, x0, x1 in (("wide pad A1/B12", 1195, 1275),
                    ("narrow pad (mid)", 2000, 2030),
                    ("wide pad B1/A12", 3105, 3185)):
    r = vspan(x0, x1, 600, 1300, 0.25)
    if r:
        print(f" pad row via {lab:18s}: rows {r[0]}..{r[1]}  "
              f"top={mm(r[0]):.4f}  bottom={mm(r[1]):.4f}  "
              f"h={(r[1]-r[0])/PX_PER_MM:.4f}  centre={mm((r[0]+r[1])/2):.4f}")

# ---- 3. shell slots: outline extents in the slot columns -------------------
for lab, x0, x1, y0, y1 in (("REAR slot (left)", 600, 690, 600, 1600),
                            ("REAR slot (right)", 3390, 3470, 600, 1600),
                            ("FRONT slot (left)", 600, 690, 1600, 2300),
                            ("FRONT slot (right)", 3390, 3470, 1600, 2300)):
    g = edges(x0, x1, y0, y1, 0.35)
    if len(g) >= 2:
        top, bot = g[0][0], g[-1][1]
        print(f" {lab:20s}: rows {top}..{bot}  top={mm(top):.4f} "
              f"bot={mm(bot):.4f}  h={(bot-top)/PX_PER_MM:.4f}  "
              f"CENTRE={mm((top+bot)/2):.4f}")

# ---- 4. NPTH round holes ---------------------------------------------------
for lab, x0, x1 in (("NPTH circle (left)", 920, 950),
                    ("NPTH circle (right)", 2115, 2145)):
    g = edges(x0, x1, 700, 1250, 0.35)
    if len(g) >= 2:
        top, bot = g[0][0], g[-1][1]
        print(f" {lab:20s}: rows {top}..{bot}  d={(bot-top)/PX_PER_MM:.4f}  "
              f"CENTRE={mm((top+bot)/2):.4f}")

# ---- 5. dimension columns: extreme arrow-tip rows ---------------------------
print("\n=== right-hand dimension columns: dark groups (arrow tips) ===")
for lab, xc in (("0.50", 2956), ("4.18", 3172), ("1.64 / 5.79", 3316)):
    g = edges(xc - 3, xc + 4, 400, 2500, 0.5)
    print(f" col {lab:12s}: " + "; ".join(
        f"{mm(a):+.4f}..{mm(b):+.4f}" for a, b in g))
