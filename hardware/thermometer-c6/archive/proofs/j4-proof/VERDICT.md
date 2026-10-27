# J4 / XUNPU FPC-05FB-24PH20 — tails-vs-mouth verdict

**Part FPC-05FB-NPH20, "FPC 0.5PH H2.0 后翻双面接" = 0.5 mm pitch, H2.0, REAR-FLIP,
dual-side contact.** Adversarial cross-check of STEP numbers + manufacturer drawing +
in-situ KiCad render. All three agree.

---

## PART A — numeric STEP analysis (objective core)

STEP is a SolidWorks AP214 export (Latin-1, needs `grep -a`). Contacts are gold
(`COLOUR_RGB 0.831,0.671,0.129`, 432 face-uses) — this lets metal be isolated from
plastic exactly. Stray construction points at z≈-14/-12/-3 dropped.

**(a) Full model bbox (clean):**
- ROW axis = **X**: −7.75 … +7.75 (15.50 mm) — the 24-contact row, 0.5 mm pitch, gold spans X ±5.83.
- DEPTH axis = **Y**: −6.80 … +0.25 (7.05 mm).
- HEIGHT = **Z**: −0.54 … +2.69 (3.23 mm ≈ H2.0 body).

**(b) The 24 gold contacts (isolated by colour):**
- Flat **SMT solder feet** (gold, z ≤ 0.10): dominant at **depth Y ≈ −0.5 … 0.0** (432 of 528 pts).
- Contact **spring tips** (gold, z = 2.34, highest): **depth Y = −4.05** (points toward the other end).
- Anchor/mounting-nail feet: **depth Y ≈ −3.25** (= 3.25 mm from the contact feet, toward −Y).

**(c) Housing opening (the mouth):**
- Depth **Y = +0.25** end = **solid wall**: 1223 pts, full height z 0…2.01 → CLOSED (rear).
- Depth **Y = −6.80** end = **thin lips**: 16 pts, z 0.15…1.79 only → OPEN slot (mouth).

**CONCLUSION (required format):**
> feet at depth **Y = −0.5…0.0**, housing spans **Y = −6.80…+0.25**, the slot opens at the
> **−6.80 face** → the SMT tails are **≈ 6.6 mm from the mouth face** and **≈ 0.25 mm from the
> rear wall**. **The tails are at the REAR (actuator) end, NOT the mouth.**

Depth order (mouth → rear): **MOUTH (−6.8) — anchor feet (−3.25) — contact tails (0.0) — rear wall (+0.25).**
The mouth is on the **anchor-row side**, opposite the contact tails. Cross-checked by isolated
STEP renders: `--side front` = open slot + ears + contacts (MOUTH); `--side back` = closed
actuator lid + gold tails (REAR).

**(3) KiCad seating** — footprint pads: contacts @ y_local = −1.625, anchors @ +1.625 (3.25 mm apart);
model offset (0, 1.35, 0), rotate 0. The in-situ render (board rot −90) puts the model's gold
tails on the **EAST contact-pad column**, actuator **EAST**, mouth **WEST** — i.e. the model is
**directionally faithful and roughly registered**. (My first hand-map that put the tails 2.7 mm
off was wrong — KiCad flips the model Y; the render is authoritative and shows them on the pads.)

---

## Physical + board mapping

| feature | connector | footprint | board (J4 @ 144.6,116.8, rot −90) |
|---|---|---|---|
| contact tails + actuator (REAR) | solder to contact pads | y_local −1.625 | **x ≈ 146.2 → EAST** |
| anchor nails | solder to anchor pads | y_local +1.625 | **x ≈ 142.9 → WEST** |
| **MOUTH (FPC entry)** | on the anchor side | beyond +1.625 | **→ WEST (board interior)** |

Board Edge.Cuts x = 100…148; **J4 is 3.4 mm from the EAST edge.** The mouth points the
**other way — WEST, into the board.**

---

## Images in this pack

- `proof_section.png` — drawing section view: actuator (top/rear), FPC/mouth (bottom), insertion 2.10, PCB face. Internal metal is genuinely hard to trace here → end/direction labels defer to Part-A numbers, flagged honestly.
- `proof_topview.png` — 18.50/5.40/4.90 top view: SMT tail row sticks out the **rear/actuator edge**; ears/nails at both ends; **mouth is the opposite edge**.
- `proof_landpattern.png` — recommended land: 24× contact pads + 2 anchor pads @ **3.25 mm**; body/mouth extend toward the **anchor** side.
- `proof_step_render.png` — in-situ KiCad render, real orientation: **actuator/tails EAST, mouth WEST** — the render tells the truth.
- `proof_board.png` — top-down board crop: contact column EAST (x≈146.2), anchors WEST, E edge 3.4 mm, **CABLE EXITS → WEST**.

---

## VERDICT

**(i) Physical tails-vs-mouth:** The SMT contact tails are on the **REAR / actuator side**.
The **mouth is on the anchor-tab side, opposite the tails.** The section-view hypothesis
("metal tail curling out at the mouth/front") is **REJECTED** — that lower-corner feature is a
mouth lip / mounting nail, not the solder tail.

**(ii) Land pattern / board orientation:** The land pattern itself is correct (verbatim from the
XUNPU drawing). But with it placed **contacts-EAST / anchors-WEST**, and the connector's mouth
sitting on the anchor side, **the mouth/cable faces WEST — into the board interior, away from the
3.4 mm-distant east edge.** The footprint's own descr claims the opposite ("cable enters from
pad-row side (y−)"). **If the intent is cable-toward-the-edge (EAST), the board is BACKWARDS**
and J4 must be re-placed rotated 180° (contacts→WEST, anchors+mouth→EAST) with its 24 nets
re-routed and pin-1 re-checked against the panel cable. Only a mechanical requirement that the
panel FPC genuinely approaches from the WEST would make the current orientation correct — that
contradicts the documented intent.

**(iii) STEP seating / the "cosmetic 180 flip":** The current render is **already directionally
correct (mouth-WEST = physical truth).** It does **NOT** need a z-rot-180. The repo comment
(`pcb_layout.py`: "STEP seats 180-deg flipped… fix = z-rot 180") is built on the false premise
that the mouth should render EAST; applying that flip would make the render **falsely** show
mouth-EAST and hide the real problem. The genuine issue is not the 3D model — it is the
**land-pattern orientation vs. the stated cable-entry intent.**

**Bottom line:** tails-at-rear ✔, mouth faces WEST ✔, and per the documented "cable-from-contact-
side (east)" intent the J4 orientation is **backwards** — catch it before fab.
