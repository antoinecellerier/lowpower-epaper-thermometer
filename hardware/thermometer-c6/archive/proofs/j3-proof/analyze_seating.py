#!/usr/bin/env python3
"""Numeric J3 USB-C STEP-vs-copper seating analysis (no GUI).

Extracts the model's 4 shell through-hole legs, 2 plastic NPTH posts and the
gold SMT tail row from the EasyEDA/JLC STEP, maps them into board coordinates
through KiCad's exact model+footprint transform, and reports peg->slot /
tail->pad residuals for the current offset and for a candidate offset.

KiCad model->board transform (front-side footprint), calibrated exactly:
  * footprint placement board = fp + Rb(theta)*local, with
      Rb(theta) = [[cos, sin],[-sin, cos]]   (verified against pcbnew pad data)
  * model->footprint-local-2D:  local2D = ( offset + Rz(-rotZ)*(scale*v) ),
    then Y is flipped (model 3D Y-up -> footprint 2D Y-down): FLIP=-1
    (validated against the known-good J4 seat).
  For J3 (theta=180, rotZ=180, scale=1, ox=0):
      board_x = 23.400 + vx
      board_y = 1.745 + oy - vy
"""
import re
import sys
import numpy as np

STEP = "local.3dmodels/USB_C_Receptacle_HRO_TYPE-C-31-M-12.step"

# ---- board-frame copper truth (pcbnew, origin (100,100)), north edge y=0 ----
FP_POS = (23.400, 1.745)
FRONT_SLOTS = [(19.08, 0.695), (27.72, 0.695)]   # drill 0.6 x 1.2
REAR_SLOTS = [(19.08, 4.875), (27.72, 4.875)]     # drill 0.6 x 1.7
NPTH_HOLES = [(20.51, 4.345), (26.29, 4.345)]     # drill 0.65 round
PAD_ROW_Y = 5.790                                  # 16 signal pads


def load_points(path):
    data = open(path, encoding="latin-1").read()
    pts = []
    for m in re.finditer(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(([^)]*)\)\s*\)", data):
        n = re.findall(r"[-+0-9.Ee]+", m.group(1))
        if len(n) == 3:
            pts.append([float(x) for x in n])
    return np.array(pts), data


def gold_points(data):
    """Isolate gold contact geometry via the STYLED_ITEM -> colour chain."""
    ent = {int(m.group(1)): m.group(2)
           for m in re.finditer(r"#(\d+)\s*=(.*?);", data, re.S)}
    refs = lambda s: [int(x) for x in re.findall(r"#(\d+)", s)]
    pid = {}
    for i, b in ent.items():
        mm = re.match(r"\s*CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(([^)]*)\)", b)
        if mm:
            n = re.findall(r"[-+0-9.Ee]+", mm.group(1))
            if len(n) == 3:
                pid[i] = [float(x) for x in n]
    fwd = {i: refs(b) for i, b in ent.items()}

    def is_gold(i):
        m = re.match(r"\s*COLOUR_RGB\s*\(\s*'[^']*'\s*,\s*([-+0-9.Ee]+)\s*,"
                     r"\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)", ent[i])
        if not m:
            return False
        r, g, bl = map(float, m.groups())
        return r > 0.6 and g > 0.4 and bl < 0.4 and r > bl + 0.4

    def walk(root, pred=None):
        seen, st, out = set(), [root], []
        while st:
            n = st.pop()
            if n in seen:
                continue
            seen.add(n)
            if pred is None and n in pid:
                out.append(pid[n])
            elif pred and pred(n):
                out.append(n)
            for c in fwd.get(n, ()):
                if c not in seen:
                    st.append(c)
        return out

    gp = []
    for i, b in ent.items():
        if b.strip().startswith("STYLED_ITEM"):
            r = refs(b)
            if not r:
                continue
            if any(is_gold(c) for s in r[:-1] for c in walk(s, is_gold)):
                gp.extend(walk(r[-1]))
    return np.array(gp)


def bbox_center(sel, axis):
    return (sel[:, axis].min() + sel[:, axis].max()) / 2


def model_features(P, G):
    """Return model-frame (x,y) centers of the 4 shell legs, 2 NPTH posts and
    the tail-foot row. Legs/posts measured on the below-board plated barrel."""
    barrel = P[(P[:, 2] > -0.55) & (P[:, 2] < -0.35)]      # clean peg cross-section
    sub = P[P[:, 2] < -0.15]
    legs = {}
    for sx in (+1, -1):
        for yc, lbl in ((0.0, "front"), (-4.175, "rear")):
            s = barrel[(np.sign(barrel[:, 0]) == sx)
                       & (np.abs(barrel[:, 0]) > 3.6)
                       & (np.abs(barrel[:, 1] - yc) < 1.5)]
            legs[(sx, lbl)] = (bbox_center(s, 0), bbox_center(s, 1))
    npth = {}
    for sx in (+1, -1):
        s = sub[(np.sign(sub[:, 0]) == sx) & (np.abs(sub[:, 0]) > 2.4)
                & (np.abs(sub[:, 0]) < 3.4) & (np.abs(sub[:, 1] + 3.675) < 0.6)]
        npth[sx] = (bbox_center(s, 0), bbox_center(s, 1))
    foot = G[(G[:, 2] < 0.06) & (G[:, 1] < -4.3)]
    tail_y = bbox_center(foot, 1)
    return legs, npth, tail_y


def to_board(vx, vy, oy):
    return (FP_POS[0] + vx, FP_POS[1] + oy - vy)


def report(legs, npth, tail_y, oy, label):
    print(f"\n=== offset oy={oy:+.3f}  ({label}) ===")
    resid = []
    slot_of = {"front": FRONT_SLOTS, "rear": REAR_SLOTS}
    for (sx, lbl), (vx, vy) in sorted(legs.items()):
        bx, by = to_board(vx, vy, oy)
        tgt = min(slot_of[lbl], key=lambda s: abs(s[0] - bx))
        d = ((bx - tgt[0]) ** 2 + (by - tgt[1]) ** 2) ** 0.5
        resid.append(d)
        print(f" shell leg {lbl:5s} x{sx:+d}: board=({bx:+.3f},{by:+.3f}) "
              f"slot=({tgt[0]:.3f},{tgt[1]:.3f}) dist={d:.3f}")
    for sx, (vx, vy) in sorted(npth.items()):
        bx, by = to_board(vx, vy, oy)
        tgt = min(NPTH_HOLES, key=lambda s: abs(s[0] - bx))
        d = ((bx - tgt[0]) ** 2 + (by - tgt[1]) ** 2) ** 0.5
        print(f" NPTH post  x{sx:+d}     : board=({bx:+.3f},{by:+.3f}) "
              f"hole=({tgt[0]:.3f},{tgt[1]:.3f}) dist={d:.3f}")
    _, tby = to_board(0.0, tail_y, oy)
    print(f" tail row center     : board_y={tby:+.3f}  pad_row_y={PAD_ROW_Y:.3f} "
          f"dy={tby - PAD_ROW_Y:+.3f}")
    print(f" max shell-leg peg->slot dist = {max(resid):.3f} mm")
    return max(resid), tby - PAD_ROW_Y


def main():
    P, data = load_points(STEP)
    G = gold_points(data)
    legs, npth, tail_y = model_features(P, G)
    print("model-frame feature centers (mm):")
    for k, v in sorted(legs.items()):
        print(f"  shell leg {k}: ({v[0]:+.3f},{v[1]:+.3f})")
    for k, v in sorted(npth.items()):
        print(f"  NPTH post  x{k:+d}: ({v[0]:+.3f},{v[1]:+.3f})")
    print(f"  tail foot row y: {tail_y:+.3f}")
    print(f"  front->rear leg spacing (model): "
          f"{abs(legs[(1,'front')][1] - legs[(1,'rear')][1]):.3f}  "
          f"(board slot spacing 4.180)")
    oy_cur = 1.35
    oy_new = float(sys.argv[1]) if len(sys.argv) > 1 else -0.94
    report(legs, npth, tail_y, oy_cur, "CURRENT / committed e22be63")
    report(legs, npth, tail_y, oy_new, "CANDIDATE")


if __name__ == "__main__":
    main()
