# J3 / USB_C_Receptacle_HRO_TYPE-C-31-M-12 — pads-vs-part orientation verdict

**Part: HRO TYPE-C-31-M-12 (LCSC C165948), 16-pin SMT horizontal USB-C receptacle,
stock upstream KiCad footprint. Placed board (23.4, 5.0) rot 0; north edge y=0.**

## VERDICT: **MISPLACED — J4-class 180° placement error.**

The copper land pattern is on the **wrong side of the connector body relative to the
north edge**. As fabricated, J3's **mouth faces SOUTH (into the board interior); the
rear/solder-tail row sits at the north edge**. A USB-C plug cannot be inserted from the
north edge. The pretty 3D preview (KiCad *and* JLC) shows the mouth overhanging the north
edge, which is what masked the error — but that is the **model**, and the model is seated
**180° off the copper** (its gold tails float ~7 mm south of the actual pads).

This is the inverse trap of J4: J4's model was faithful and a comment was wrong; here the
**model looks right and the copper is wrong**.

---

## The one-line proof (model-independent, from the genuine HRO datasheet)

- Genuine HRO dimensioned drawing (LCSC C165948, drawn 2020-12-08), **"RECOMMEND P.C.B
  LAYOUT (COMPONENT SIDE)"**: the 16-tail pad row is **5.79 mm from the PCB EDGE**, with
  the connector body/mouth **between the pads and the edge** (mouth overhangs the edge).
  The four shell legs straddle the depth; the **larger legs are at the rear (next to the
  tails)**, the smaller ones at the front/mouth.
- **Our board:** the copper pad row is **0.955 mm from the north edge**, and the body
  extends the **other way** (south, y = 1.35 … 8.65).
- The tails of this part are 5.79–6.8 mm from its mouth. Pads only 0.955 mm from the
  insertion edge is **geometrically impossible** for mouth-at-edge (the mouth would float
  ~4.8 mm off the board). So pads-at-0.955-mm can only mean **mouth-into-board (south)**.
  → The connector is flipped 180°.

---

## PART A — footprint copper (pcbnew, board frame; y=0 = north edge, +y = south interior)

| feature | board-frame y | note |
|---|---|---|
| north board edge | **0.000** | straight edge, no notch/cutout at J3's x |
| 16 SMT signal pads (A1..B12) | **0.955** | 0.955 mm from edge — the whole row |
| shell SH pads, **big** (1×2.1) | 1.870 | = REAR pair (near tails) per datasheet |
| plastic peg holes (Ø0.65) | 2.400 | just inboard of pads (rear) |
| F.Fab body | 1.35 … 8.65 | 7.3 mm deep, all SOUTH of the pads |
| shell SH pads, small (1×1.6) | 6.050 | = FRONT/mouth pair |
| model gold tails render at | ~8.3 … 9.2 | SOUTH — NOT on the copper pads |

Footprint-internal geometry is **correct and self-consistent with the datasheet**
(pads + big legs + pegs cluster at local −y = rear; small legs at local +y = mouth).
The footprint is fine; it is **placed backwards on the board**: at rot 0 its rear
(local −y) faces the north edge and its mouth (local +y) faces south.

## PART B — STEP model numeric analysis (JLC C165948 model, the one the board renders)

STEP = AP214, gold contacts isolated by colour `RGB 0.949,0.761,0.180` (152 faces),
shell grey `0.851`. Colour→geometry associated by BFS over the entity graph.

- **Gold SMT solder tails** (flat, z ≈ 0): model **Y = −5.30 … 0.00** → the REAR row.
- **Gold spring tips** (z ≈ 1.95, grip the plug on the tongue): model Y = −0.65 … 1.85.
- **Mouth opening** is at model **+Y** (beyond the tips); shell front ≈ +5.2.
- Tails (−Y) and mouth (+Y) are at **opposite ends**, ~7 mm apart → the model matches the
  datasheet (rear tails).
- KiCad transform (verified by the calibrated top render): model −Y → **board SOUTH**,
  so the model's mouth (+Y) → **board NORTH**. The model therefore renders mouth-north
  (overhanging the edge), while its gold tails render ~7.4 mm south of the copper pads.
- In the footprint's local frame: copper pads at **local −y**, model gold tails at
  **local +y** → the JLC model is **180° misregistered** (its `rotate` should be
  `(0,0,180)`; the `offset (0,1.35,0)` cannot fix a rotation).

## PART C — why prior verification passed

Two errors cancelled in the preview:
1. **Placement (fabrication-critical):** footprint at rot 0 → rear pad row at the north
   edge, mouth into the board.
2. **Model registration (cosmetic):** JLC model 180° off the pads → its mouth renders at
   the north edge.

The mis-registered model showed the mouth where the *intended* edge is, so "mouth renders
north/off-edge" was confirmed against the **model** while the **copper** was reversed. The
`edge-clearance-usb-c` DRU exception silenced DRC on the courtyard/silk crossing the north
edge — but the thing crossing the edge is the **rear** (silk top at y=−0.295), not the mouth.

---

## Quantified mismatch

- Orientation: **180° wrong** (mouth faces south; must face/overhang north).
- Pad-row position: **0.955 mm** from the north edge; datasheet requires **5.79 mm**
  (mouth side). Off by **4.84 mm** and on the wrong side of the body.

## Fix (STOP — no repo changes made; user decides)

This is an **orientation** problem, not a tails-side problem — the standard rear-tail part
is exactly what you want, so **re-place, do not swap the part**:

1. Rotate J3 **180°** and shift it **~3.25 mm north** (anchor y 5.0 → ~1.75) so the pad
   row lands **5.79 mm from the edge** and the mouth overhangs the north edge by ~1.9 mm.
2. Re-route the USB nets (VBUS, D+, D−, CC1, CC2, GND; SBU1/2 NC) — the fan-out flips.
3. Re-check CC1/CC2 and pin-1 after the flip.
4. Set the model block `rotate (0,0,180)` so the 3D/JLC preview matches the copper
   (otherwise the next preview will look "wrong" while the copper is finally right).

**Catch before fab/assembly** — as built, J3 is an unpluggable connector facing the
board interior.

---

## Images in this pack
- `proof_pads.png` — board-frame pad map: rear pad row 0.96 mm from the north edge, body
  + mouth pointing south (red), datasheet's required 5.79 mm (yellow). Shell legs green.
- `proof_overlay.png` — model gold tails (south) vs copper pads (north): ~7.4 mm apart,
  the model is seated 180° off the land pattern (the preview lies).
- `proof_model.png` — objective STEP projection: gold SMT tails at −Y (rear), mouth at +Y,
  opposite ends; the 16-tail row and the model→board axis mapping.
- `proof_datasheet.png` — the genuine HRO recommended PCB layout: pad row 5.79 mm from the
  PCB EDGE (mouth side), annotated against our 0.955 mm.
