# J3 USB-C 3D-model seating — numeric correction

Part **HRO TYPE-C-31-M-12** (LCSC C165948), footprint
`Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`, placed board (23.400, 1.745)
rot 180 (mouth-north). Origin (100,100), north edge y=0. The copper is
datasheet-correct and untouched; this fixes only the `MODELS_3D["J3"]` seating.

Model STEP: `local.3dmodels/USB_C_Receptacle_HRO_TYPE-C-31-M-12.step`
(EasyEDA/JLC, AP214, mm). Analysis: `archive/proofs/j3-proof/analyze_seating.py`.

## Correction

| field    | before (e22be63) | after       |
|----------|------------------|-------------|
| offset   | `(0, 1.35, 0)`   | `(0, -0.94, 0)` |
| rotate   | `(0, 0, 180)`    | `(0, 0, 180)` (unchanged) |
| scale    | `(1, 1, 1)`      | `(1, 1, 1)` |

Only **oy** changes: **Δoy = −2.29 mm** (model moves 2.29 mm north). ox stays 0
because x registers exactly (connector is x-symmetric, so the 180° flip about x
is exact); no dz — the gold SMT feet already sit on z=0 (board top).

## Why a 180° z-rotation alone mistranslates this model

The EasyEDA STEP's origin is **not** at the land pattern's centroid — it sits at
the connector's front-shell reference, ~2.3 mm south of the pattern centre. A
z-rotation of 180° pivots the whole body about that off-centre origin (every
depth coord y → −y about the origin, not about the body centre), so it lands the
body translated by ~2× the origin offset. The pre-flip offset `(0, 1.35, 0)` was
right for the un-rotated model; after the flip the depth offset must be
**re-derived in the rotated frame** — hence oy 1.35 → −0.94.

## KiCad model→board transform (calibrated, not assumed)

Footprint placement `board = fp + Rb(θ)·local`, with
`Rb(θ)=[[cosθ, sinθ],[−sinθ, cosθ]]` — verified to the nm against every J3/J4 pad
via `pad.GetFPRelativePosition()`. Model→footprint-local: KiCad applies
`Rz(−rotZ)` to the model, adds the mm offset, then flips Y (3D Y-up → footprint
2D Y-down, FLIP=−1, validated against the known-good J4 seat). For J3
(θ=180, rotZ=180, ox=0):

```
board_x = 23.400 + vx
board_y =  1.745 + oy − vy
```

## Model-frame feature centres (mm) and residuals after fix (oy = −0.94)

Shell-leg centres from the below-board plated barrel (z≈−0.45); tail from the
gold SMT feet (colour-isolated via STYLED_ITEM→COLOUR_RGB).

| model feature        | model (x, y)      | board target       | landed (x, y)      | dist |
|----------------------|-------------------|--------------------|--------------------|------|
| shell leg front x−   | (−4.320, +0.000)  | slot (19.080,0.695)| (19.080, 0.805)    | 0.110 |
| shell leg front x+   | (+4.320, +0.000)  | slot (27.720,0.695)| (27.720, 0.805)    | 0.110 |
| shell leg rear  x−   | (−4.320, −4.175)  | slot (19.080,4.875)| (19.080, 4.980)    | 0.105 |
| shell leg rear  x+   | (+4.320, −4.175)  | slot (27.720,4.875)| (27.720, 4.980)    | 0.105 |
| NPTH post x−         | (−2.890, −3.675)  | hole (20.510,4.345)| (20.510, 4.480)    | 0.135 |
| NPTH post x+         | (+2.890, −3.675)  | hole (26.290,4.345)| (26.290, 4.480)    | 0.135 |
| SMT tail-foot row    | y = −4.875        | pad row y = 5.790  | y = 5.680          | 0.110 |

**Max shell-peg→slot 0.110 mm; tail row 0.110 mm; NPTH 0.135 mm — all < 0.15 mm.**
(Before, oy=+1.35: every peg 2.40 mm south of its slot, tail 2.18 mm south.)

## Right variant — not a mismatch

- x registration is exact: shell legs ±4.320 → slots 27.72/19.08; NPTH posts
  ±2.890 → holes 26.29/20.51; 16 gold contacts span the pad row.
- model front→rear leg span **4.175 mm** vs land pattern **4.180 mm** (Δ0.005).
- mouth at model +Y, tails at model −Y — structurally correct.

The one apparent tension: registering the 4 pegs exactly gives oy=−1.048, at which
the tail-foot **centre** lands at board y=5.57 — 0.22 mm north of the pad centre
5.79. That is not a variant conflict: the model's solder foot (0.85 mm long) is
shorter than the 1.45 mm pad, and at oy=−1.048 the foot **heel** meets the pad
heel within 0.08 mm — the pad's extra length is the standard south toe extension
for the solder fillet. Seating at oy=−0.94 balances that residual so the 4 pegs
**and** the tail-foot centre both fall within 0.15 mm.

## Renders (this folder)

- `top_north_edge.png` — top: mouth overhangs the north edge, tails on the south
  pad row, the 4 yellow shell slots flank the body.
- `side_west_low.png` — low-angle view from the west (user viewpoint): the mouth
  overhangs the board edge, body seated flush.
- `seating_after.png` / `seating_before.png` — matched NW oblique; before
  (e22be63) the body floats ~2.4 mm south with the shell slots exposed north of
  it, after it seats on the edge with the slots under the shell tabs.
