# J3 SMT land vs the measured solder foot — verdict

**Our land is MARGINAL AT THE HEEL, not deficient.** The solder foot measures
**0.850 mm** long (measured, not assumed — the old 0.85 guess was right), our pad
covers all of it, but with only **+0.080 mm heel protrusion** — below IPC-7351B's
*Least*-material heel (0.25) and **negative** under a realistic tolerance stack,
while spending **+0.520 mm** on toe (near IPC *Most*).
**Recommend a pad-Y-only shift of 0.170 mm toward the mouth** (size, width, x and
pitch all unchanged) **plus NPTH ⌀0.65 → ⌀0.60**, giving heel **+0.250** / toe
**+0.350**. Fold it into the respin the j3-datum +1.415 mm move already forces;
on its own it is not worth re-routing J3 for.

---

## 0. Two corrections to the brief's premises (both verified)

* **This connector has 12 SMT contacts, not 16.** The KiCad footprint has 16 pad
  *entries* because four positions carry two names each (A1/B12, A12/B1, A4/B9,
  A9/B4 are co-located). 12 physical pads = HRO's `4-0.60` + `8-0.30`.
* **The NPTH row: ours is right and the *drawing* is the outlier.** The brief's
  table says ours is −0.022 off. Measured from the STEP, the post is a
  ⌀0.500 cylinder whose axis is at **3.650** behind the front peg — *exactly*
  our footprint's 3.650. HRO's drawing says 3.6716. The prior −3.675 figure came
  from bounding-boxing a point cluster that included the post's off-centre barb
  tip at y −3.750; the cylinder's own axis is unambiguous.

---

## 1. How the foot was isolated (and how it was *not*)

The board-contacting face was found by three conditions that must all hold — no
z-slicing of a point cloud, no guessing where the flat part ends:

1. the face is **gold** (`STYLED_ITEM → COLOUR_RGB 0.949/0.761/0.180`), i.e. a
   contact and not the shell or housing;
2. its surface is a **`PLANE` whose normal is parallel to Z** (|n·ẑ| > 0.999),
   i.e. flat and horizontal — not the bend arc, not a side wall;
3. its plane origin sits at **z = 0** (tolerance 1×10⁻⁴ mm; the model is exact —
   every gold z quantises to 0.0000 or 0.2000, so the tolerance is not load
   bearing).

That yields **exactly 12 faces**, one per contact. Each is a 4-vertex rectangle.
The tail is 0.200 mm thick, so the second set of Z-normal planes (z = 0.200) is
the *top* of the same tails and is correctly excluded.

**The feet ARE co-planar and board-contacting**, so the question the brief raised
("say so if they are not") does not arise. Cross-checked on one contact by
walking its complete face list and its side-wall edge loop, which gives the exact
profile:

```
(5.300, z 0.0) ──flat 0.850──> (4.450, z 0.0) ──CIRCLE r=0.200,
                                centre (4.450, z 0.200)──> (4.250, z 0.200)
```

So beyond the heel the underside lifts off **tangentially** along a 0.200 mm
radius, reaching full tail height 0.200 mm at datum 4.250. The board-plane
footprint of that arc — **the heel-fillet zone — is 0.200 mm long.**

**Nothing obstructs it.** Over the bend window there is no material of any colour
between z = 0.26 and z ≈ 1.98 (≈1.7 mm of clear headroom), and the tail rises as
an exposed vertical riser. A heel fillet will form and will be AOI-visible *if
the land is there to feed it*.

### False positive caught (worth recording)

A raw `CARTESIAN_POINT` census shows apparent below-board material at
(|x| 3.10–3.25, y −4.55…−4.70, z −0.851) — outside every hole in our footprint,
i.e. an apparent collision. **It is not real.** Those points are
`AXIS2_PLACEMENT_3D` / `LINE` parameterisation origins; **no `ADVANCED_FACE` owns
a vertex there** (the owning faces live at z ≈ +3.0). Restricting the census to
face vertices leaves only the 4 shell legs and 2 NPTH posts. *Any STEP analysis in
this project that bounding-boxes `CARTESIAN_POINT`s inherits this bug* — see §7,
where it turns out to have produced a real error on J4.

---

## 2. Measured foot (STEP, all 12 contacts)

| quantity | value |
|---|---|
| foot length min / max / mean | **0.8500 / 0.8500 / 0.8500** mm (spread 0.0000) |
| — 4 contacts 0.400 mm wide | 0.8500 |
| — 8 contacts 0.200 mm wide | 0.8500 |
| foot **heel** (near the mouth), from front shell slot centre | **4.450** |
| foot **toe** (tail tip), from front shell slot centre | **5.300** |
| tail thickness | 0.200 |
| bend radius / heel-fillet zone length | 0.200 / **0.200** |
| contact x centres | ±3.225, ±2.450, ±1.750, ±1.250, ±0.750, ±0.250 |

**Foot length does not differ between the 0.3 mm and 0.6 mm pad groups** — all
twelve are the same 0.850 mm.

Datum chain re-derived independently from face vertices (front peg axis = 0):
rear peg **4.175** (drawing 4.1716), NPTH post **3.650** (drawing 3.6716),
foot heel 4.450, foot toe 5.300 (drawing pad far edge 5.3040 → Δ **0.004**).

---

## 3. Coverage — three lands vs the measured foot

All referenced to the **front shell slot centre**, +ve = away from the mouth.
Third reference fetched with `easyeda2kicad --footprint --lcsc_id C165948` into a
scratch dir (not installed, not wired into the generator).

| land | heel | toe | length | heel-fillet zone covered | min side margin (0.6 pads) | (0.3 pads) |
|---|---|---|---|---|---|---|
| **ours** — KiCad stock, IPC toe-extended | **+0.080** | +0.520 | 1.450 | **40 %** | **0.075** | 0.050 |
| **HRO** drawing nominal | +0.283 | **+0.004** | 1.137 | 100 % (+0.083) | 0.049 | 0.044 |
| **EasyEDA / JLC** (C165948) | +0.160 | +0.290 | 1.300 | 80 % | 0.050 | 0.050 |
| *proposed (see §5)* | *+0.250* | *+0.350* | *1.450* | *100 % (+0.050)* | *0.075* | *0.050* |

All three fully cover the foot at nominal; none leaves foot unsupported.

**The two vendor references agree with each other and disagree with us in the
same direction**: both put the heel further toward the mouth than we do
(4.167 / 4.290 vs our 4.370). That is the substantive finding.

### x axis — here *ours is the best of the three*

| pad | ours | HRO drawing | EasyEDA | contact (measured) |
|---|---|---|---|---|
| outer 0.6 | ±3.250 | ±3.196 (nom 3.20) | ±3.20 | ±3.225 |
| inner 0.6 | ±2.450 | ±2.392 (nom 2.40) | ±2.40 | ±2.450 |
| 0.3 pads | ±1.75/1.25/0.75/0.25 | ±1.745/1.245/0.750/0.250 | same as ours | ±1.750/1.250/0.750/0.250 |

Per-pad side margins (inboard/outboard): ours **0.075/0.125** and **0.100/0.100**;
HRO **0.124/0.074** and **0.149/0.049**. KiCad's ±3.25/±2.45 centres the measured
contacts better than HRO's own ±3.20/±2.40. **Keep our x.**

*(The drawing's X datum was taken from the pad set's mirror centreline and then
validated against features not used to build it: NPTH circles land at ±2.887
(nominal 2.890) and shell slots at ±4.316 (nominal 4.320) — good to 0.004 mm.)*

*(EasyEDA's four wide pads are `gr_poly` custom pads: outline 0.600 × 1.300 with a
`width 0.1` stroke, which KiCad renders as 0.700 × 1.400. The 0.600/1.300 intent
is used above; the stroke is an `easyeda2kicad` conversion artifact.)*

---

## 4. IPC-7351B judgement and tolerance stack

Reference values (**quoted from the standard, the only numbers here that are not
measured**) — gull-wing land protrusion, pitch ≤ 0.625 mm:

| level | toe JT | heel JH | side JS |
|---|---|---|---|
| Most | 0.55 | 0.45 | 0.01 |
| Nominal | 0.35 | 0.35 | −0.02 |
| Least | 0.15 | 0.25 | −0.04 |

| land | toe | heel | side |
|---|---|---|---|
| **ours** | +0.520 → Nominal…Most | **+0.080 → BELOW Least by 0.170** | +0.075 → ≥ Most |
| HRO | **+0.004 → BELOW Least by 0.146** | +0.283 → Least…Nominal | +0.049 → ≥ Most |
| EasyEDA | +0.290 → Least…Nominal | +0.160 → BELOW Least by 0.090 | +0.050 → ≥ Most |

### Stack on the heel (worst case, y)

| ± | term |
|---|---|
| 0.075 | **part→board registration**: ⌀0.500 post in our ⌀0.650 NPTH. *Measured*, and it dominates — the shell slots are far looser (front peg 0.80 in a 1.20 slot = ±0.20; rear ±0.325), so the NPTH is the locator. |
| 0.050 | part internal (foot vs locating post). **ASSUMED** — not on HRO's drawing. |
| 0.050 | fab pad-edge position (etch + registration). **ASSUMED.** |
| **0.175** | worst-case sum. JLC's ±0.05 placement is *not* additive: the part is pinned by its pegs, so placement error is absorbed by the peg/hole slop already counted. HRO's `TOLERANCE FOR PCB LAYOUT IS ±0.05` is an instruction to the layout engineer, not a part tolerance; our land is generated, so it does not apply to us. |

| land | nominal | − registration only | − reg + fab | − all three |
|---|---|---|---|---|
| **ours** | +0.080 | **+0.005** | **−0.045** | **−0.095** |
| HRO | +0.283 | +0.208 | +0.158 | +0.108 |
| EasyEDA | +0.160 | +0.085 | +0.035 | −0.015 |
| *proposed* | *+0.250* | *+0.200* (slack halves to ±0.050 with ⌀0.60) | *+0.150* | *+0.100* |

**Reading:** the registration term alone consumes our entire heel budget. Worst
case the pad heel sits ~0.045–0.095 mm *inside* the foot, so the heel of the foot
lands on soldermask and no heel fillet forms.

**Why this is "marginal" and not "deficient":** even worst case we lose <0.1 mm of
an 0.850 mm foot, so joint area and conductivity are never at risk; and the
mechanical load of plugging/unplugging is carried by the **four through-hole shell
legs in plated slots**, not by the signal contacts. The cost of leaving it is a
weak/absent heel fillet on the 12 signal joints — an IPC-compliance and
AOI-inspectability problem, and a fatigue-life reduction on a part that gets
levered — not a likely field failure. Also note the pads are `roundrect`
(rratio 0.25): at the contact's own x edges the pad heel is a further 0.009 (0.6
pads) / 0.004 (0.3 pads) short, so the corner heel margin is ~0.071 not 0.080.

---

## 5. Recommendation

**Do not adopt HRO's land wholesale**, and **do not keep ours unchanged.**

* HRO's land is rejected on two counts: **zero toe fillet** (+0.004, below IPC
  Least by 0.146 — bad for AOI/X-ray, which reads the toe fillet), and its
  hole-to-copper is only **0.195 mm** (their ⌀0.60 NPTH at 3.6716 vs pad heel
  4.1667), under both our board's 0.25 mm `hole_clearance` and JLC's ~0.254 mm
  DFM minimum.
* Ours is rejected on the heel, per §4.

### The binding constraint

The pad heel cannot move freely toward the mouth — it runs into the NPTH hole:

| NPTH ⌀ | min pad heel (0.25 mm hole clearance) | max achievable heel protrusion |
|---|---|---|
| 0.65 (today) | 4.225 | 0.225 |
| **0.60** (HRO's own drawing value) | **4.200** | **0.250** |
| 0.55 | 4.175 | 0.275 |

⌀0.60 on a ⌀0.500 post keeps 0.050 mm radial slack — vendor-specified, and it
**halves the dominant tolerance term** as a bonus.

### Exact geometry

**Shift the pad row 0.170 mm toward the mouth. Do not change pad size, width, x,
pitch, shape, or the shell slots.** Reduce the NPTH to ⌀0.60.

| | now | proposed |
|---|---|---|
| pad heel / toe (from front shell slot centre) | 4.370 / 5.820 | **4.200 / 5.650** |
| pad size | 0.6 × 1.45 and 0.3 × 1.45 | **unchanged** |
| pad x | ±3.25, ±2.45, ±1.75, ±1.25, ±0.75, ±0.25 | **unchanged** |
| footprint-local pad y (stock frame, front slot at +1.05) | −4.045 | **−3.875** |
| NPTH | ⌀0.65 at local y −2.60 | **⌀0.60**, position unchanged |
| board pad row y, current placement (fp 23.400,1.745,180) | 5.790 | **5.620** (span 4.895…6.345) |
| board pad row y, after the j3-datum +1.415 move | 7.205 | **7.035** (span 6.310…7.760) |

Result: heel **+0.250** (IPC Least, exactly), toe **+0.350** (IPC Nominal,
exactly), side unchanged at 0.075/0.050 (both ≥ IPC Most), heel-fillet zone
**100 % covered** with 0.050 to spare beyond the riser base, hole-to-copper
**0.250** (at the rule), heel worst case **+0.100**.

### When to do it

**Only as part of the J3 respin.** The j3-datum verdict already requires
`PLACE["J3"]` (23.4, 1.745, 180) → (23.4, 3.160, 180), which invalidates all of
J3's copper (VBUS 43 segs, both data pairs, both CC nets, the shell GND
stitching) plus the neighbours in the destination band. Moving the pads a further
0.170 mm inside that same respin is nearly free. As a standalone change it would
force the same re-route for a defect that is unlikely to actually fail — not
worth it.

### What else it touches

* **The footprint must be forked into `local.pretty/`.** It is currently
  **stock**: `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`, resolved from
  `${KICAD10_FOOTPRINT_DIR}/Connector_USB.pretty` — not a local file. `fp-lib-table`
  already has `local` → `${KIPRJMOD}/local.pretty`, so the fork is
  `local:USB_C_Receptacle_HRO_TYPE-C-31-M-12`. That fpid change ripples to:
  * `generator/circuit.py:65` `footprint=` string;
  * `generator/pcb_layout.py` `MODELS_3D` — **keyed by fpid string**, so the
    `"Connector_USB:…"` key must be re-keyed to `"local:…"` or the 3D model
    silently stops being applied;
  * regenerated schematic/netlist → `make check`, then DRC, then `make fab`
    (CPL/BOM/rotation checklist) and `ORDERING.md`'s J3 confirmation.
* **`MODELS_3D["J3"]`'s offset `(0, −0.94, 0)`**: a pads-only change does **not
  invalidate it** — the offset is footprint-local and registers against the pegs
  and posts, none of which move. But its *justification* changes, and it should
  be corrected anyway. `oy = −0.94` is a **compromise**: `archive/proofs/j3-proof/` records
  that registering the four pegs exactly wants **−1.048**, and that −0.94 was
  chosen to split the 0.22 mm difference against the *current* pad row. That
  0.22 mm residual **is exactly this land error** — with the pads at 5.620 the
  model needs no fudge. The exact peg-registered value is **oy = −1.050**
  (front peg model y = 0 → board 0.695 = 1.745 + oy). At −1.050 the model's feet
  land at 4.450/5.300 from the datum by construction, i.e. inside the proposed
  pad with heel 0.250 / toe 0.350 — pegs, posts and feet all register at once.
* **New DRC watch item**: pad heel to NPTH hole becomes 0.250 mm, exactly at
  `m_HoleClearance`. Verify with a real DRC run on the respin; if it flaps, the
  project's scoped-rule idiom (`hv-clearance-j4`, `edge-clearance-usb-c`) is the
  precedent, but prefer not to waive — back the shift off to 0.150 (heel +0.230)
  rather than relax a fab rule.
* Not affected: courtyard, silk, shell slots and their copper, the
  `edge-clearance-usb-c` waiver (which the +1.415 move removes anyway).

---

## 6. Sanity-check of the brief's table

| feature | ours | HRO drawing | STEP model | note |
|---|---|---|---|---|
| rear slot centre | 4.180 | 4.1716 | 4.175 | agrees |
| NPTH post centre | 3.650 | 3.6716 | **3.650** | **ours matches the part, drawing is the outlier** |
| SMT pad heel | 4.370 | 4.1667 | (foot heel 4.450) | confirmed |
| SMT pad toe | 5.820 | 5.3040 | (foot toe 5.300) | confirmed |
| SMT pad height | 1.450 | 1.1373 | (foot 0.850) | confirmed |

The brief's "0.85 mm is an ASSUMPTION" is now **measured and correct**, and its
consequence is confirmed: our heel margin is 0.080, HRO's 0.283.

---

## 7. J4 (XUNPU FPC-05FB-24PH20, C2856831) — separate finding

Compared `local.pretty/XUNPU_FPC-05FB-24PH20.kicad_mod` against the EasyEDA/JLC
footprint and against `local.3dmodels/XUNPU_FPC-05FB-24PH20.step`.

**The land is correct — every pad matches to rounding:**

| feature | ours | EasyEDA | Δ |
|---|---|---|---|
| 24 signal pads | 0.300 × 1.200, pitch 0.500, x ±5.75…±0.25, y −1.625 | identical, y −1.62 | 0.005 (2 dp rounding) |
| anchor pads | 2.000 × 1.800 at (±7.300, +1.625) | identical, y +1.62 | 0.005 |
| pad 1 position | x = +5.75 | x = +5.75 | — |
| signal-to-anchor row span | 3.250 | 3.240 | 0.010 |

Also confirmed against the STEP: gold z = 0 faces at 0.500 mm pitch, foot length
0.700, contact x centres ±5.75…, matching the pad row.

**But the body outline is ~1.6 mm too deep, and the earlier proof is why:**

| | ours (F.Fab) | EasyEDA silk | STEP (face vertices) |
|---|---|---|---|
| body depth | **7.050** | 5.400 | **5.400** |
| from pad row to the mouth face | **6.550** | 5.500 | **4.950** |
| from pad row to the rear wall | 0.500 | 0.100 | 0.450 |

Our footprint's `descr` cites "mouth slot lips 6.55 mm away (numeric STEP proof,
`archive/proofs/j4-proof/`)", and `archive/proofs/j4-proof/VERDICT.md` places the mouth at model
Y = −6.80. **That −6.80 does not exist in the geometry.** The STEP's face-vertex
bbox is Y[−5.150, +0.250]; the points at Y = −6.802 and −8.193 (and X = −11.114,
Z = −14.039) are referenced only by `LINE` and `AXIS2_PLACEMENT_3D` entities —
**zero of them are `VERTEX_POINT`s**. Same class of artifact as §1. The rear wall
(+0.25) agrees, so only the mouth-side extent is wrong.

Consequences (reported, **not changed**, per instruction): `F.Fab` and `F.CrtYd`
overstate J4's depth by ~1.65 mm on the mouth side, so the courtyard reserves
board area that is not physically occupied, and the `descr`'s 6.55 mm figure
should be 4.95 mm. The **180° orientation conclusion of `archive/proofs/j4-proof/` is
unaffected** — it rests on which end is open, not on how far away it is, and the
rear wall / tail relationship still holds.

---

## 8. Files

| file | what |
|---|---|
| `land-proof.png` | the proof image — 920 px per mm of part, equal aspect. **A** side elevation: measured foot profile (flat 0.850 + r=0.200 arc) with all four lands as bars and every heel/toe margin dimensioned; **B** plan of the outer 0.600 pad / 0.400 contact; **C** plan of a 0.300 pad / 0.200 contact |
| `step_parse.py` | minimal STEP AP214 entity parser (entities, refs, points, directions, colours, face→surface/normal/vertices) |
| `feet.py` | the isolation described in §1 → `feet.json` (12 foot rectangles) |
| `bend.py` | every gold face touching z=0; the 12 bend cylinders; one contact's complete face list and side-wall profile |
| `context.py`, `below_and_above.py` | heel-fillet headroom, below-board census |
| `mystery_boss.py` | the §1 false positive, resolved |
| `datum_and_clearance.py` | datum chain re-derivation |
| `drawing_pads.py`, `drawing_datum_x.py` | HRO drawing pad X positions + X-datum validation (reuses `archive/proofs/j3-datum/objects.py`) |
| `analyse.py` | coverage table, IPC judgement, tolerance stack, recommended geometry |
| `proof_image.py` | renders `land-proof.png` |

EasyEDA footprints were fetched to a scratch directory outside the repo and are
**not** installed in `local.pretty/` or referenced by the generator.

*No project file outside `archive/proofs/j3-land/` was modified. No commits.*
