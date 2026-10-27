#!/usr/bin/env python3
"""archive/proofs/j3-land/land-proof.png -- one representative contact at true scale.

Three panels, all sharing the depth axis and all drawn with equal aspect
(1 mm across == 1 mm down), so every gap on the page is a real gap:

  A  side elevation of the contact (measured STEP profile: flat foot, r=0.200
     bend arc, 0.200 thick tail) over the board plane, with the candidate
     lands drawn as bars in the board plane and every heel/toe margin
     dimensioned.
  B  plan view of the outer 0.600 mm pad / 0.400 mm contact (A1/B12, GND).
  C  plan view of a 0.300 mm pad / 0.200 mm contact (A6, D+).

Datum: FRONT shell slot centre = 0, increasing to the right = away from the
connector mouth.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.path import Path
import matplotlib.patches as mpatches

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "land-proof.png")

# ------------------------------------------------------------ measured (STEP)
FOOT_HEEL, FOOT_TOE = 4.450, 5.300
BEND_END = 4.250
THK, R = 0.200, 0.200

# name, heel, toe, colour, wide_w, wide_x, narrow_w, roundrect ratio
LANDS = [
    ("ours - KiCad stock", 4.370, 5.820, "#1f6feb", 0.600, 3.25, 0.300, 0.25),
    ("HRO drawing nominal", 4.1667, 5.3040, "#d1242f", 0.598, 3.20, 0.299, 0.0),
    ("EasyEDA / JLC C165948", 4.290, 5.590, "#1a7f37", 0.600, 3.20, 0.300, 0.0),
]
PROPOSED = ("PROPOSED (ours, shifted 0.170)", 4.200, 5.650, "#8250df",
            0.600, 3.25, 0.300, 0.25)
ALL = LANDS + [PROPOSED]

CON_WX, CON_WW = 3.225, 0.400
CON_NX, CON_NW = 0.250, 0.200

X0, X1 = 3.74, 5.92
MM = 4.6                      # inches of page per mm of part


def roundrect_path(x0, x1, y0, y1, r):
    if r <= 0:
        return Path([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
                    [Path.MOVETO] + [Path.LINETO] * 3 + [Path.CLOSEPOLY])
    pts, codes = [], []
    corners = [((x1 - r, y0), (x1, y0), (x1, y0 + r)),
               ((x1, y1 - r), (x1, y1), (x1 - r, y1)),
               ((x0 + r, y1), (x0, y1), (x0, y1 - r)),
               ((x0, y0 + r), (x0, y0), (x0 + r, y0))]
    pts.append((x0 + r, y0)); codes.append(Path.MOVETO)
    for a, c, b in corners:
        pts += [a, c, b]; codes += [Path.LINETO, Path.CURVE3, Path.CURVE3]
    pts.append((x0 + r, y0)); codes.append(Path.CLOSEPOLY)
    return Path(pts, codes)


def dim(ax, x0, x1, y, txt, colour, ha="center", fs=8.6):
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<|-|>", color=colour, lw=1.0,
                                shrinkA=0, shrinkB=0, mutation_scale=7))
    xt = {"center": (x0 + x1) / 2, "left": x0, "right": x1}[ha]
    ax.text(xt, y + 0.014, txt, ha=ha, va="bottom", fontsize=fs, color=colour,
            fontweight="bold",
            bbox=dict(fc="white", ec="none", alpha=0.9, pad=0.7))


ROWS = [-0.11, -0.265, -0.420, -0.575]
BH = 0.030                     # bar half-height

hA, hB, hC = 1.10, 0.80, 0.46
fig = plt.figure(figsize=((X1 - X0) * MM + 2.4, (hA + hB + hC) * MM + 4.0))
gs = fig.add_gridspec(3, 1, height_ratios=[hA, hB, hC],
                      left=0.075, right=0.985, top=0.855, bottom=0.055,
                      hspace=0.26)
axA, axB, axC = (fig.add_subplot(gs[i]) for i in range(3))

# =========================================================== A side elevation
ax = axA
ax.set_xlim(X0, X1); ax.set_ylim(-0.66, 0.44); ax.set_aspect("equal")
ax.add_patch(Rectangle((X0, -0.66), X1 - X0, 0.66, fc="#eef1f4", ec="none"))
ax.axhline(0, color="#24292f", lw=1.8, zorder=5)
ax.text(X1 - 0.02, -0.022, "PCB surface  z = 0", fontsize=8.5, color="#57606a",
        va="top", ha="right")

ax.add_patch(Rectangle((BEND_END, 0), FOOT_HEEL - BEND_END, 0.44,
                       fc="#ffd8a8", ec="none", alpha=0.6, zorder=1))
ax.text(BEND_END - 0.012, 0.425,
        "heel-fillet zone 0.200\n(bend arc r=0.200, board-plane footprint)",
        fontsize=8, color="#9a6700", ha="right", va="top", linespacing=1.25)

t = np.linspace(-np.pi / 2, -np.pi, 80)
arc = np.column_stack([FOOT_HEEL + R * np.cos(t), R + R * np.sin(t)])
prof = np.vstack([[[FOOT_TOE, 0.0], [FOOT_HEEL, 0.0]], arc, [[FOOT_TOE, THK]]])
ax.add_patch(Polygon(prof, closed=True, fc="#e3b341", ec="#7d4e00", lw=1.4,
                     zorder=4))
ax.text(5.24, THK / 2, "contact, measured from the STEP\n"
                       "(flat foot z=0, then r=0.200 arc)",
        fontsize=8.4, ha="right", va="center", color="#5c3d00",
        linespacing=1.25, zorder=6)

for xv, lab in ((FOOT_HEEL, "foot heel 4.450"), (FOOT_TOE, "foot toe 5.300")):
    for a in (axA, axB, axC):
        a.axvline(xv, color="#7d4e00", lw=1.1, ls=(0, (5, 3)), zorder=3)
    ax.text(xv, 0.415, lab, fontsize=8.8, color="#7d4e00", ha="center",
            va="top", fontweight="bold",
            bbox=dict(fc="white", ec="none", alpha=0.9, pad=0.9))
ax.axvline(BEND_END, color="#9a6700", lw=0.9, ls=":", zorder=3)
dim(ax, FOOT_HEEL, FOOT_TOE, 0.265, "measured foot 0.850", "#7d4e00")

for (name, h, tt, col, *_), yy in zip(ALL, ROWS):
    ax.add_patch(Rectangle((h, yy - BH), tt - h, 2 * BH, fc=col, ec="none",
                           alpha=0.92, zorder=6))
    ax.text((h + tt) / 2, yy, name, fontsize=8.8, color="white",
            fontweight="bold", ha="center", va="center", zorder=8)
    dim(ax, h, FOOT_HEEL, yy + BH + 0.020, f"heel {FOOT_HEEL-h:+.3f}", col,
        ha="right")
    dim(ax, FOOT_TOE, tt, yy + BH + 0.020, f"toe {tt-FOOT_TOE:+.3f}", col,
        ha="left")

ax.set_title("A   side elevation - measured solder foot vs the candidate lands"
             "   (true scale: 1 mm across = 1 mm down)",
             fontsize=11, loc="left", pad=10)
ax.set_ylabel("z  (mm)", fontsize=9)

# ============================================== B plan, outer 0.600 mm pad
ax = axB
ax.set_xlim(X0, X1); ax.set_ylim(CON_WX - 0.44, CON_WX + 0.40)
ax.set_aspect("equal")
for name, h, tt, col, w, px, _nw, rr in ALL:
    ls = (0, (6, 3)) if name.startswith("PROPOSED") else "-"
    ax.add_patch(mpatches.PathPatch(
        roundrect_path(h, tt, px - w / 2, px + w / 2, rr * min(w, tt - h)),
        fc="none", ec=col, lw=1.8, ls=ls, zorder=5))
ax.add_patch(Rectangle((FOOT_HEEL, CON_WX - CON_WW / 2), FOOT_TOE - FOOT_HEEL,
                       CON_WW, fc="#e3b341", ec="#7d4e00", lw=1.4, zorder=4))
ax.text((FOOT_HEEL + FOOT_TOE) / 2, CON_WX, "measured foot  0.850 x 0.400",
        fontsize=8.8, ha="center", va="center", color="#5c3d00", zorder=6)

# side-margin callouts, drawn where every land is present
for xa, y0, y1, col, txt, va in (
        (4.86, CON_WX - CON_WW / 2, 3.25 - 0.300, "#1f6feb", "ours 0.075", "top"),
        (5.10, CON_WX + CON_WW / 2, 3.20 + 0.299, "#d1242f", "HRO 0.074", "bottom")):
    ax.annotate("", xy=(xa, y0), xytext=(xa, y1),
                arrowprops=dict(arrowstyle="<|-|>", color=col, lw=1.1,
                                mutation_scale=7))
    ax.text(xa + 0.02, (y0 + y1) / 2, txt, fontsize=8.4, color=col,
            va="center", fontweight="bold",
            bbox=dict(fc="white", ec="none", alpha=0.9, pad=0.7))
ax.text(X0 + 0.02, CON_WX - 0.42,
        "ours |x|=3.250 (contact |x|=3.225)   HRO & JLC |x|=3.200",
        fontsize=8.4, color="#57606a", va="bottom")
ax.set_title("B   plan - outer 0.600 mm pad / 0.400 mm contact (A1/B12, GND); "
             "ours centres the contact better in x than HRO's",
             fontsize=11, loc="left", pad=10)
ax.set_ylabel("board |x|  (mm)", fontsize=9)

# ============================================== C plan, 0.300 mm pad
ax = axC
ax.set_xlim(X0, X1); ax.set_ylim(CON_NX - 0.24, CON_NX + 0.24)
ax.set_aspect("equal")
for name, h, tt, col, _w, _px, nw, rr in ALL:
    ls = (0, (6, 3)) if name.startswith("PROPOSED") else "-"
    ax.add_patch(mpatches.PathPatch(
        roundrect_path(h, tt, CON_NX - nw / 2, CON_NX + nw / 2,
                       rr * min(nw, tt - h)),
        fc="none", ec=col, lw=1.8, ls=ls, zorder=5))
ax.add_patch(Rectangle((FOOT_HEEL, CON_NX - CON_NW / 2), FOOT_TOE - FOOT_HEEL,
                       CON_NW, fc="#e3b341", ec="#7d4e00", lw=1.4, zorder=4))
ax.text((FOOT_HEEL + FOOT_TOE) / 2, CON_NX, "0.850 x 0.200", fontsize=8.8,
        ha="center", va="center", color="#5c3d00", zorder=6)
ax.set_title("C   plan - 0.300 mm pad / 0.200 mm contact (A6, D+); "
             "all four lands share x here, side margin 0.050",
             fontsize=11, loc="left", pad=10)
ax.set_ylabel("board |x|  (mm)", fontsize=9)
ax.set_xlabel("depth from the FRONT shell slot centre  (mm)"
              "     <-- left = toward the connector mouth / north board edge",
              fontsize=9.5)

for a in (axA, axB, axC):
    a.grid(True, color="#d0d7de", lw=0.4, alpha=0.7)
    a.set_axisbelow(True)
    a.tick_params(labelsize=8.5)

handles = [mpatches.Patch(fc="#e3b341", ec="#7d4e00",
                          label="measured solder foot - STEP face geometry; "
                                "all 12 contacts identical, 0.850 long")]
for name, h, tt, col, *_ in ALL:
    ls = "--" if name.startswith("PROPOSED") else "-"
    handles.append(mpatches.Patch(
        fc="none", ec=col, lw=1.8, ls=ls,
        label=f"{name}:  heel {FOOT_HEEL-h:+.3f}   toe {tt-FOOT_TOE:+.3f}   "
              f"length {tt-h:.3f}"))
fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.072, 0.972),
           fontsize=10, frameon=False, handlelength=2.4)
fig.suptitle("J3  HRO TYPE-C-31-M-12  -  SMT land vs the measured solder foot",
             fontsize=14, fontweight="bold", x=0.072, ha="left", y=0.992)
fig.text(0.072, 0.878,
         "IPC-7351B gull-wing land protrusion, pitch <= 0.625 mm  -  "
         "heel JH: Least 0.25 / Nominal 0.35 / Most 0.45      "
         "toe JT: Least 0.15 / Nominal 0.35 / Most 0.55",
         fontsize=9.5, color="#57606a")

fig.savefig(OUT, dpi=200, facecolor="white")
print("wrote", OUT, f"-- {MM*200:.0f} px per mm of part")
