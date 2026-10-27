#!/usr/bin/env python3
"""J3 land analysis: coverage of the MEASURED solder foot by three lands.

Datum for every number: the FRONT shell slot centre, +ve = away from the
connector mouth (i.e. deeper into the board).  All three lands and the STEP
model are reduced to that one datum so they are directly comparable.

Inputs
  measured (this analysis)  : archive/proofs/j3-land/feet.py   -- STEP face geometry
  ours                      : /usr/share/kicad/footprints/Connector_USB.pretty/
                              USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod
  HRO drawing               : archive/proofs/j3-datum/ (vector) + archive/proofs/j3-land/drawing_pads.py
  EasyEDA/JLC C165948       : easyeda2kicad --footprint (scratch, gitignored)
"""
import json

# ------------------------------------------------------------------ MEASURED
# STEP, gold ADVANCED_FACEs, PLANE surface, Z normal, plane origin z=0.
FOOT_HEEL = 4.450          # all 12 contacts, exactly
FOOT_TOE = 5.300           # all 12 contacts, exactly
FOOT_LEN = FOOT_TOE - FOOT_HEEL
BEND_END = 4.250           # underside reaches z=0.200 here (r=0.200 arc)
ARC = FOOT_HEEL - BEND_END  # 0.200 board-plane length of the heel-fillet zone
CONTACT_W = {"wide": 0.400, "narrow": 0.200}
CONTACT_X = {"wide": (3.225, 2.450), "narrow": (1.750, 1.250, 0.750, 0.250)}

# ---------------------------------------------------------------- THE LANDS
# (heel, toe, wide-pad |x| centres, wide-pad width, narrow |x|, narrow width)
LANDS = {
    "ours (KiCad stock, IPC toe-extended)":
        dict(heel=4.370, toe=5.820,
             wx=(3.25, 2.45), ww=0.600,
             nx=(1.75, 1.25, 0.75, 0.25), nw=0.300, round_r=0.25),
    "HRO drawing nominal":
        dict(heel=4.1667, toe=5.3040,
             wx=(3.20, 2.40), ww=0.598,
             nx=(1.745, 1.245, 0.750, 0.250), nw=0.299, round_r=0.0),
    "EasyEDA / JLC (C165948)":
        dict(heel=4.290, toe=5.590,
             wx=(3.20, 2.40), ww=0.600,
             nx=(1.75, 1.25, 0.75, 0.25), nw=0.300, round_r=0.0),
}

# IPC-7351B gull-wing land protrusion, pitch <= 0.625mm.  QUOTED FROM THE
# STANDARD -- these three rows are the only numbers here that are not measured.
IPC = {"Most": (0.55, 0.45, 0.01),
       "Nominal": (0.35, 0.35, -0.02),
       "Least": (0.15, 0.25, -0.04)}     # (toe JT, heel JH, side JS)


def side_margins(pad_x, pad_w, con_x, con_w):
    """(inboard, outboard) copper margin between a pad and its contact."""
    p0, p1 = pad_x - pad_w / 2, pad_x + pad_w / 2
    c0, c1 = con_x - con_w / 2, con_x + con_w / 2
    return c0 - p0, p1 - c1


def main():
    print("=" * 78)
    print("MEASURED FOOT (STEP model, per-contact face geometry)")
    print("=" * 78)
    rows = json.load(open("archive/proofs/j3-land/feet.json"))
    lens = [round(r["y1"] - r["y0"], 6) for r in rows]
    wids = [round(r["x1"] - r["x0"], 6) for r in rows]
    print(f"  contacts measured        : {len(rows)}")
    print(f"  foot length  min/max/mean: {min(lens):.4f} / {max(lens):.4f} / "
          f"{sum(lens)/len(lens):.4f} mm   (spread {max(lens)-min(lens):.4f})")
    for w in sorted(set(wids)):
        sel = [l for l, q in zip(lens, wids) if q == w]
        print(f"    contacts {w:.3f} mm wide (n={len(sel)}): foot length "
              f"{min(sel):.4f}..{max(sel):.4f}")
    print(f"  foot heel / toe from datum: {FOOT_HEEL:.4f} / {FOOT_TOE:.4f}")
    print(f"  heel-fillet zone (bend arc, r=0.200): datum {BEND_END:.3f}"
          f"..{FOOT_HEEL:.3f} = {ARC:.3f} mm long")

    print()
    print("=" * 78)
    print("COVERAGE OF THE MEASURED FOOT  (mm; + = pad extends beyond the foot)")
    print("=" * 78)
    hdr = (f"{'land':38s} {'heel':>7} {'toe':>7} {'len':>6} {'arc cov':>9} "
           f"{'side(0.6)':>10} {'side(0.3)':>10}")
    print(hdr)
    print("-" * len(hdr))
    for name, L in LANDS.items():
        hp = FOOT_HEEL - L["heel"]
        tp = L["toe"] - FOOT_TOE
        sw = min(min(side_margins(px, L["ww"], cx, CONTACT_W["wide"]))
                 for px, cx in zip(L["wx"], CONTACT_X["wide"]))
        sn = min(min(side_margins(px, L["nw"], cx, CONTACT_W["narrow"]))
                 for px, cx in zip(L["nx"], CONTACT_X["narrow"]))
        cov = min(hp, ARC) / ARC * 100
        print(f"{name:38s} {hp:+7.3f} {tp:+7.3f} {L['toe']-L['heel']:6.3f} "
              f"{cov:8.0f}% {sw:10.3f} {sn:10.3f}")

    print()
    print("  per-pad side margins (inboard / outboard), contact inside pad:")
    for name, L in LANDS.items():
        print(f"   {name}")
        for px, cx in zip(L["wx"], CONTACT_X["wide"]):
            a, b = side_margins(px, L["ww"], cx, CONTACT_W["wide"])
            print(f"      wide  pad |x|={px:.3f} contact |x|={cx:.3f}: "
                  f"{a:+.3f} / {b:+.3f}")
        for px, cx in zip(L["nx"], CONTACT_X["narrow"]):
            a, b = side_margins(px, L["nw"], cx, CONTACT_W["narrow"])
            print(f"      narrow pad |x|={px:.3f} contact |x|={cx:.3f}: "
                  f"{a:+.3f} / {b:+.3f}")

    print()
    print("=" * 78)
    print("IPC-7351B GULL-WING LAND PROTRUSION (pitch <= 0.625mm) -- QUOTED")
    print("=" * 78)
    print(f"{'level':10s} {'toe JT':>8} {'heel JH':>8} {'side JS':>8}")
    for k, (t, h, s) in IPC.items():
        print(f"{k:10s} {t:8.2f} {h:8.2f} {s:8.2f}")
    print()
    for name, L in LANDS.items():
        hp = FOOT_HEEL - L["heel"]
        tp = L["toe"] - FOOT_TOE
        sw = min(min(side_margins(px, L["ww"], cx, CONTACT_W["wide"]))
                 for px, cx in zip(L["wx"], CONTACT_X["wide"]))

        def band(v, key):
            t = {k: IPC[k][key] for k in IPC}
            if v >= t["Most"]:
                return ">= Most"
            if v >= t["Nominal"]:
                return "Nominal..Most"
            if v >= t["Least"]:
                return "Least..Nominal"
            return f"BELOW Least by {t['Least']-v:.3f}"
        print(f"  {name}")
        print(f"     toe  {tp:+.3f}  -> {band(tp,0)}")
        print(f"     heel {hp:+.3f}  -> {band(hp,1)}")
        print(f"     side {sw:+.3f}  -> {band(sw,2)}")

    print()
    print("=" * 78)
    print("TOLERANCE STACK ON THE HEEL (y, worst case)")
    print("=" * 78)
    terms = [("part->board registration: NPTH d0.500 post in our d0.650 hole",
              0.075),
             ("part internal (foot vs locating post) -- ASSUMED, not published",
              0.050),
             ("fab: pad edge position (etch + registration) -- ASSUMED", 0.050)]
    for t, v in terms:
        print(f"   +/-{v:.3f}   {t}")
    tot = sum(v for _, v in terms)
    print(f"   -------")
    print(f"   +/-{tot:.3f}   worst-case sum "
          f"(JLC's +/-0.05 placement is absorbed by the pegs, not additive)")
    print()
    print(f"{'land':38s} {'nominal':>9} {'-reg only':>10} {'-reg-fab':>10} {'-all':>8}")
    for name, L in LANDS.items():
        hp = FOOT_HEEL - L["heel"]
        print(f"{name:38s} {hp:+9.3f} {hp-0.075:+10.3f} {hp-0.125:+10.3f} "
              f"{hp-tot:+8.3f}")

    print()
    print("=" * 78)
    print("RECOMMENDATION -- shift the pad row toward the mouth; size unchanged")
    print("=" * 78)
    NPTH_DATUM = 3.650            # measured: post axis, and our footprint's hole
    HOLE_CLEAR = 0.25             # board DesignSettings m_HoleClearance
    print(f"  binding constraint: pad heel vs the NPTH hole "
          f"(hole_clearance = {HOLE_CLEAR} mm)")
    print(f"  NPTH centre at datum {NPTH_DATUM:.3f}; "
          f"pad heel must be >= {NPTH_DATUM:.3f} + r + {HOLE_CLEAR:.2f}")
    print(f"{'NPTH dia':>9} {'min pad heel':>13} {'max heel protrusion':>21}")
    for d in (0.65, 0.60, 0.55, 0.50):
        h = NPTH_DATUM + d / 2 + HOLE_CLEAR
        print(f"{d:9.2f} {h:13.3f} {FOOT_HEEL-h:21.3f}")
    print()
    print("  HRO's own layout accepts a smaller gap: their NPTH d0.60 @3.6716,")
    print(f"  pad heel 4.1667 -> hole-to-copper "
          f"{4.1667-(3.6716+0.30):.3f} mm (under JLC's ~0.254 DFM minimum).")
    print()
    SHIFT = 0.170
    NEW_D = 0.60
    heel = LANDS["ours (KiCad stock, IPC toe-extended)"]["heel"] - SHIFT
    toe = LANDS["ours (KiCad stock, IPC toe-extended)"]["toe"] - SHIFT
    print(f"  PROPOSED: pads shift {SHIFT:.3f} toward the mouth, "
          f"NPTH d0.65 -> d{NEW_D:.2f}")
    print(f"     pad heel {heel:.3f}  toe {toe:.3f}  length {toe-heel:.3f} "
          f"(unchanged)")
    print(f"     heel protrusion {FOOT_HEEL-heel:+.3f}  (IPC Least 0.25)")
    print(f"     toe  protrusion {toe-FOOT_TOE:+.3f}  (IPC Nominal 0.35)")
    print(f"     bend-arc coverage {min(FOOT_HEEL-heel,ARC)/ARC*100:.0f}%"
          f"  (+{FOOT_HEEL-heel-ARC:.3f} beyond the riser base)")
    print(f"     hole-to-copper  {heel-(NPTH_DATUM+NEW_D/2):.3f} mm")
    print(f"     registration slack now +/-{(NEW_D-0.500)/2:.3f} "
          f"(was +/-0.075) -> heel worst case "
          f"{FOOT_HEEL-heel-(NEW_D-0.500)/2-0.05-0.05:+.3f}")
    print()
    print("  footprint-local (stock frame, front slot at y=+1.05):")
    print(f"     pads   y -4.045 -> {1.05 - heel - (toe-heel)/2:+.3f}   "
          f"size 0.6/0.3 x 1.45 UNCHANGED, x UNCHANGED")
    print(f"     NPTH   d0.65 -> d0.60 at y -2.60 (unchanged position)")
    print("  board frame, current placement (fp 23.400,1.745,180; "
          "front slots y 0.695):")
    print(f"     pad row y 5.790 -> {0.695+heel+(toe-heel)/2:.3f} "
          f"(span {0.695+heel:.3f}..{0.695+toe:.3f})")
    print("  board frame, after the j3-datum +1.415 move (front slots y 2.110):")
    print(f"     pad row y -> {2.110+heel+(toe-heel)/2:.3f} "
          f"(span {2.110+heel:.3f}..{2.110+toe:.3f})")
    print()
    print("  3D model: peg-exact offset is oy=-1.048 (archive/proofs/j3-proof/), at which")
    foot_ctr_board = 1.745 - 1.048 + (FOOT_HEEL + FOOT_TOE) / 2 + 0.695 - 0.695
    print(f"     the foot centre lands at board y "
          f"{1.745-1.048+4.875:.3f}; the proposed pad centre is "
          f"{0.695+heel+(toe-heel)/2:.3f}")
    print(f"     -> residual {0.695+heel+(toe-heel)/2-(1.745-1.048+4.875):+.3f}"
          f" = exactly (toe-heel protrusion)/2 = "
          f"{((toe-FOOT_TOE)-(FOOT_HEEL-heel))/2:+.3f}, as intended.")


if __name__ == "__main__":
    main()
