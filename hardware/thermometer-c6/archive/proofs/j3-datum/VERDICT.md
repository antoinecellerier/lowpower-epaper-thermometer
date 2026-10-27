# J3 (HRO TYPE-C-31-M-12) — where does the 5.79 datum actually land?

## VERDICT

**MUST MOVE 1.415 mm SOUTH.**  `PLACE["J3"]` y: **1.745 → 3.160** (x and the 180°
rotation unchanged).

Neither reading (a) nor reading (b) is right. **"5.79" is measured from the
PCB EDGE to the ⌀0.60 NPTH plastic-post CENTRELINE**, not to the SMT pad row at
all — the pad row is tied to that same datum by the two short dimensions
**"1.64"** (pad far edge) and **"0.50"** (pad near edge) stacked above it in the
same column. The pad-row centreline therefore sits **6.843 mm** from the PCB
EDGE, and **"4.18" is shell-slot centre to shell-slot centre**, putting the
front shell slot **2.108 mm** from the PCB EDGE (not 1.61, not 0.695).

---

## 1. How the numbers were obtained

* **Method 1 (primary, exact).** The page content streams of
  `datasheets/HRO_TYPE-C-31-M-12_datasheet.pdf` were parsed directly
  (`pdf_vector.py`), composing the full `q/Q/cm` CTM stack, so every segment is
  in page space. AutoCAD emitted the whole sheet on an integer grid of
  **0.12 pt**, so coordinates are exact, not sampled. The sheet is drawn rotated
  (page `/Rotate 270`); the reading frame used below is `DX = -y_pdf` (right),
  `DY = -x_pdf` (down).
* **Method 2 (independent cross-check).** Page rendered at **1200 dpi**
  (`raster_check.py`) and the same features re-measured by pixel scanning.
* **Method 3 (independent physical).** `local.3dmodels/USB_C_Receptacle_HRO_TYPE-C-31-M-12.step`
  point cloud sliced by z (`step_truth.py`) — manufacturer geometry for the PART.

### Scale calibration — and it does **not** use 5.79 or 4.18

Scale is **12.24 pt/mm**, fixed by extension-line separations of dimensions that
play no part in the verdict:

| drawn dim | measured separation | → mm | error |
|---|---|---|---|
| `2.50` | 30.600 pt | 2.5000 | **0.0000** |
| `3.50` | 42.840 pt | 3.5000 | **0.0000** |
| `4.80` | 58.680 pt | 4.7941 | −0.0059 |
| `5.78` | 70.680 pt | 5.7745 | −0.0055 |
| `6.40` | 78.120 pt | 6.3824 | −0.0176 |
| `8.65` | 105.720 pt | 8.6373 | −0.0127 |
| `0.50` pad pitch | 6.120 pt | 0.5000 | **0.0000** |
| `4-0.60` pad width | 7.320 pt | 0.5980 | −0.0020 |
| `8-0.30` pad width | 3.60–3.72 pt | 0.294–0.304 | ≤0.006 |

The drawing itself is only good to ~±0.02 mm (it is quantised to 0.0098 mm/unit
and HRO rounded the labels); every conclusion below has ≥1.0 mm of margin.

### "PCB EDGE" is not in doubt

`DY = -431.720` is (i) the only full-width horizontal line in the view
(183.24 pt + 16.08 pt, spanning the whole layout), (ii) the line HRO's own
**"PCB EDGE"** leader arrow terminates on — leader arrow tip measured at
`(DX -355.880, DY -431.720)` — and (iii) where the `5.79` dimension's lower
arrow tip lands. See `datum-proof.png`.

---

## 2. Where each dimension actually terminates (arrow tips, both methods)

All arrow tips were located as filled 3-vertex paths and reduced to their tip
vertex. Values in mm **above the PCB EDGE line**.

| drawn label (verbatim) | upper tip | lower tip | span | = label? | upper tip touches | lower tip touches |
|---|---|---|---|---|---|---|
| **`5.79`** | **5.7745** | **0.0000** | 5.7745 | 5.79 ✓ | **⌀0.60 NPTH post centreline** (measured 5.7794, Δ0.005) | **PCB EDGE** |
| **`4.18`** | **6.2745** | **2.0980** | 4.1765 | 4.18 ✓ | **rear shell-slot centre** (6.2794, Δ0.005) — coincident with the pad row's near edge (6.2745, Δ0.000) | **front shell-slot centre** (2.1078, Δ0.010) |
| `1.64` | 7.4118 | 5.7745 | 1.6373 | 1.64 ✓ | pad row **far** edge | NPTH centreline |
| `0.50` | 6.2745 | 5.7745 | 0.5000 | 0.50 ✓ | pad row **near** edge | NPTH centreline |

Consistency: `1.64 − 0.50 = 1.14` = the measured pad height **1.1373**. The three
dimensions form one chain off a single datum line at 5.7745, which is the
⌀0.60 hole centreline (5.7794 measured — half a drawing unit away; nothing else
is within 0.5 mm of it).

**Honest statement of the one residual ambiguity:** `4.18`'s *upper* terminus is
numerically indistinguishable between "rear slot centre" and "pad row near
edge" — those two features coincide to 0.005 mm in this land pattern. It does
not matter: `4.18`'s *lower* terminus is unambiguous (front slot **centre** at
2.1078; that slot's own edges are at 2.9510 and 1.2647, nowhere near 2.0980),
and every feature position below was measured directly against the PCB EDGE
rather than inferred from a label.

**Reading (a) is refuted:** the pad-row centreline measures **6.8431** mm from
the PCB EDGE = 5.79 **+ 1.053**. **Reading (b)'s 1.61 mm is also wrong:** the
front shell slot centre is **2.108** mm from the PCB EDGE.

---

## 3. Methods 1 / 2 / 3 agreement

Vector vs raster (1 raster px = 0.0049 mm):

| feature | vector | raster @1200 dpi | Δ |
|---|---|---|---|
| pad row far edge | 7.4118 | 7.4118 | 0.0000 |
| pad row centreline | 6.8431 | 6.8407 | 0.0024 |
| pad row near edge | 6.2745 | 6.2696 | 0.0049 |
| rear slot centre | 6.2794 | 6.2770 | 0.0024 |
| NPTH post centre | 5.7794 | 5.7770 | 0.0024 |
| front slot centre | 2.1078 | 2.1054 | 0.0024 |
| `5.79` upper tip | 5.7745 | 5.7745 | 0.0000 |
| `4.18` lower tip | 2.0980 | 2.0980 | 0.0000 |

STEP model vs drawing, in the part's own frame (front peg axis = 0; peg
cross-sections taken at z = −0.45, i.e. inside the board, not at the barbed
tips at z = −0.85):

| chain link | STEP model | drawing (measured) | Δ |
|---|---|---|---|
| front peg → rear peg | 4.175 | 4.1716 | 0.0034 |
| front peg → NPTH post | 3.675 | 3.6716 | 0.0034 |
| front peg → tail tip / pad far edge | 5.300 | 5.3040 | 0.0040 |
| shell width | 8.940 (±4.470) | 8.9216 (`8.94` in the front view) | 0.018 |
| shell depth | 7.294 | 7.3333 (`7.35` in the front view) | 0.039 |
| peg pitch across | ±4.320 → 8.640 | `8.64` / `8.65` | ✓ |
| NPTH pitch across | ±2.890 → 5.780 | 5.7745 (`5.78`) | 0.006 |

**All three methods agree to ≤0.005 mm on the drawing and ≤0.004 mm between the
drawing and the physical part.** The 4.18 / 3.675 / 5.30 triple matching the
STEP to 4 µm is what proves the *identification* (which oval is front, which is
rear, and that the "slot centre" reading of 4.18 is correct) — it cannot be a
coincidence of two independent sources.

---

## 4. The table

Our board's north board edge is the Edge_Cuts **line centreline at y = 0.000**
(the −0.05 in the brief is half of the 0.1 mm outline width that
`GetBoundingBox()` adds — verified: the outline is `(0,0)-(48,0)`, w=0.100).

### 4a. Mechanical / locating features — these decide the placement

| feature | datasheet from PCB EDGE (mm) | ours from Edge_Cuts (mm) | delta (south) |
|---|---|---|---|
| front shell slot centre | **2.1078** (nom 2.11) | 0.695 | **+1.413** |
| rear shell slot centre | **6.2794** (nom 6.29) | 4.875 | **+1.404** |
| ⌀0.60 NPTH post centre | **5.7794** (nom 5.79) | 4.345 | **+1.434** |
| front→rear slot span | 4.1716 (`4.18`) | 4.180 | +0.008 (footprint OK) |
| front→NPTH span | 3.6716 | 3.650 | −0.022 (footprint) |

Aligning the two shell-slot rows to nominal gives **exactly +1.415 mm** for both
(2.11 − 0.695 = 1.415; 6.29 − 4.875 = 1.415). The NPTH then lands 0.030 short of
nominal — absorbed by our ⌀0.65 hole around the model's ⌀0.50 post (0.075 mm
radial slack) and pre-existing, not introduced by the move.

### 4b. SMT land — our footprint deliberately differs (do **not** align on this)

| feature | datasheet from PCB EDGE (mm) | ours from Edge_Cuts (mm) | delta |
|---|---|---|---|
| pad row far (north) edge | 7.4118 | 6.515 | +0.897 |
| pad row CENTRELINE | 6.8431 | 5.790 | +1.053 |
| pad row near (south) edge | 6.2745 | 5.065 | +1.210 |
| pad height | 1.1373 (`1.64`−`0.50`) | 1.450 | +0.313 |

The stock KiCad `USB_C_Receptacle_HRO_TYPE-C-31-M-12` land is an **IPC-style
pad with a toe extension**: 1.45 mm long vs HRO's minimal 1.14 mm, sitting
0.36 mm further from the mouth. Measured against the STEP model's solder foot
(tip at 5.300 behind the front peg, foot ≈0.85 long), the KiCad pad spans
4.370…5.820 behind the front peg — it fully covers the foot and adds 0.52 mm of
toe fillet. That is correct and intended; it is **not** a placement datum. Align
on §4a, and the pad row lands at 7.205 from the edge.

### 4c. Edge relationships

| quantity | as placed | after +1.415 | datasheet |
|---|---|---|---|
| front shell **pad** (1.00×1.60) nearest edge | **−0.105 (pad hangs off the board)** | +1.310 | — |
| front shell **drill** (0.6×1.2) → edge web | **0.095 mm** | **1.510 mm** | 1.41 (0.6×1.4 drill @ 2.11) |
| mouth face overhang past the edge (STEP) | 1.905 | **0.490** | 0.49 |
| mouth face overhang past the edge (F.Fab) | 1.950 | **0.535** | — |

**The 0.095 mm edge web and the pad literally overhanging the board edge are the
two `copper_edge_clearance` DRC errors that `make fab` currently WAIVES** as
"J3 edge-launch USB-C shell pads" (`out/drc.json`: PTH pad SH of J3 at
y = 100.695 vs the Edge.Cuts segment, ×2). They are not an inherent property of
an edge-launch connector — they are the symptom of this placement error. After
the move both disappear on their own.

---

## 5. What changes if it moves

`generator/pcb_layout.py`: `PLACE["J3"]` **(23.4, 1.745, 180) → (23.4, 3.160, 180)**.

Resulting board-frame y (x unchanged):

| feature | now | after |
|---|---|---|
| footprint anchor | 1.745 | **3.160** |
| front shell slots | 0.695 | 2.110 |
| NPTH posts | 4.345 | 5.760 |
| rear shell slots | 4.875 | 6.290 |
| 16 SMT pads | 5.790 | 7.205 (span 6.480…7.930) |
| F.CrtYd | −2.405…7.015 | −0.990…8.430 |
| F.Fab body | −1.95…5.44 | −0.535…6.855 |

Copper invalidated (all of it has to be re-routed):

* **J3's own nets** — `VBUS` 43 segs / 44.2 mm, `Net-(J3-D+-PadA6)` 10 segs,
  `Net-(J3-D--PadA7)` 10 segs, `Net-(J3-CC1)` 7 segs, `Net-(J3-CC2)` 2 segs,
  plus the shell-pad `GND` stitching.
* **Copper already sitting in the destination band** (x 18.0–28.8, y 6.0–9.6):
  `EPD_BUSY` (3 segs + 1 via), `EPD_CS` (4 segs + 1 via), 2 `GND` F.Cu segs and
  1 `Net-(J3-CC1)` via — all now under the connector.
* GND pour re-fill along the north edge.

Not affected: courtyards stay clear (nearest neighbours U3 y≥9.595, R1/R2
y≥9.655 → 1.17 mm gap; R3 is an x-neighbour, unchanged). `MODELS_3D["J3"]`
`offset (0,-0.94,0) rotate (0,0,180)` needs **no** change — it is
footprint-local and rides along. `fab_cpl.py` outputs, the rotation checklist
and `ORDERING.md`'s J3 confirmation need regenerating.

---

## 6. Files

| file | what |
|---|---|
| `datum-proof.png` | the real layout view with every measured datum drawn on it and the `5.79` / `4.18` / `1.64` / `0.50` arrow-tip terminations circled |
| `side-by-side.png` | datasheet land / our board as placed / our board moved +1.415, all at 204 px/mm aligned on PCB EDGE |
| `pdf_vector.py` | content-stream parser (CTM composed) → `vector.json` |
| `lines.py`, `features.py`, `objects.py`, `dims.py` | line/object/feature extraction in the layout view |
| `arrows.py` | arrow-tip (dimension termination) extraction |
| `raster_check.py` | independent 1200 dpi raster measurement |
| `step_truth.py` | STEP point-cloud analysis of the part |
| `make_images.py` | the two proof images |

Verbatim dimension text confirmed by rendering the glyph outlines at 1200 dpi
(the sheet has no live text — AutoCAD vectorised it): `5.79`, `4.18`, `1.64`,
`0.50`, `8.65`, `6.40`, `5.78`, `4.80`, `3.50`, `2.50`, `1.50`, `4-0.60`,
`8-0.30`, `2.00`, `1.70`, `1.40`, `0.90`, `0.60`, `⌀0.60`, `PCB EDGE`,
`RECOMMEND P.C.B LAYOUT(COMPONENT SIDE)`, `TOLERANCE FOR PCB LAYOUT IS ± 0.05`,
and in the front view `7.35`, `8.94`.

*No project file outside `archive/proofs/j3-datum/` was modified. No commits.*
