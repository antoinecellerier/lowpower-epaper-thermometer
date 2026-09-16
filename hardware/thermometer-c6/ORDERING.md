# Ordering — thermometer-c6 at JLCPCB

Order checklist for the `make fab` bundle. The fab pipeline (render → DRC →
gerbers/drill → CPL/BOM → zip → `verify/check_fab.py`) is the mechanism;
this file is the human procedure around it. Settled fab decisions live in
[`CLAUDE.md`](CLAUDE.md) ("Settled decisions — don't re-ask").

## 1. Generate & upload

- [ ] Check out the ordering commit on a **clean tree** and run `make fab`.
      A dirty tree is refused so the `rev A <hash> <date>` silk stamp names the
      exact committed source (`FAB_FORCE=1` overrides but makes the stamp a lie
      — don't ship one).
- [ ] Upload `out/fab/thermometer-c6-gerbers-<hash>-<date>.zip` (12 files:
      9 gerbers + drill + drill-map + job) to the JLCPCB quote page.

## 2. Board fabrication options

- [ ] Dimensions **48×35mm**, **2 layers**, **1.6mm**, outer copper **1oz**,
      qty **≥5**, solder mask **white** with black silk (deliberate,
      2026-07-20), TG **≥135**.
- [ ] **Surface finish: ENIG.** Chosen for flat pads under the 0.5mm-pitch
      LGA-10 sensor and the 0.5mm FPC — the board sits at JLC's 0.20mm HASL
      clearance floor, so HASL bumps are a risk there.
- [ ] **Via Covering: "Epoxy Filled & Capped" (POFV) — REQUIRED.** The
      via-in-pad escapes depend on it; the 0.3mm via drills are within JLC's
      fill limit.
- [ ] **Mark on PCB: keep "Remove Mark"** (2026 UI: a strict two-way choice
      vs "2D barcode (Serial Number)"; removal is now free and the default —
      the legacy "Order Number (Specify Position)" flow no longer exists).
      Leave the 2D-barcode serial option unset (it needs a reserved 2×10mm
      solid silk square this board doesn't have). The board carries **no
      order-mark token**: JLC support confirmed 2026-07-20 that the
      specify-position service "is already unavailable", so the
      `JLCJLCJLCJLC` back-silk string was deleted from
      `generator/pcb_layout.py` rather than shipped as a stale artifact whose
      only two outcomes were "silently scrubbed" or "printed literally".

## 2b. Confirmations raised for the 2026-07-20 order

Drafted 2026-07-18; the order was paid 2026-07-20 and the boards landed
2026-07-29. Every item is closed. The dispositions taken and the as-built
state are the archive's
[known items carried into the order](archive/README.md#order-2026-07-20--the-rev-a-production-order-first-order);
the J3 datum and land derivation is recorded there too.

| Item | Raised | Disposition | Closed |
|---|---|---|---|
| `JLCJLCJLCJLC` order-mark token under "Remove Mark" | 2026-07-18 | Token deleted from `generator/pcb_layout.py`: per JLC support the order-number-at-a-specified-position service "is already unavailable", so the token risked only printing literally on back silk | 2026-07-20 |
| J4 (FPC-05FB) geometry and routing | 2026-07-18 | Re-placed mouth-east; pads renumbered, pad 1 = panel circuit 1 north, `circuit.py` unchanged; depth 5.40 (README "BOM"); fanout re-routed, DRC clean; pin 1 and mouth continuity-verified on board 1 | respin 2026-07-19, depth corrected 2026-07-20 |
| J3 (USB-C) orientation | 2026-07-18 | Re-placed mouth-north (`out/j3-proof/`): the rot-0 placement faced the mouth into the board, masked by a 3D model mis-registered 180° | respin 2026-07-19 |
| J3 (USB-C) datum, land and routing | 2026-07-20 | Datum moved 1.415mm south and the land forked; copper re-routed, 0 unconnected, 0 dangling; the ~1.3mm preview offset is a JLC model-seating artifact. As built: the archive known items above | respin 2026-07-20 |
| D1 (CHG LED) CPL delta reset to 0 by the J3 reroute (rot 90 → 180), voiding its 2026-07-18 LED_0603 preview verification | 2026-07-20 | Resolved without a re-walk: its `0` was preview-verified 2026-07-18 (cathode cue S), and a rotation delta corrects a footprint↔library convention offset, so it is independent of the placement change. | 2026-07-20 |

The J3 clause stays in the PCBA Remark (§3) and Confirm Parts Placement stays
Yes: they cost nothing, leave a paper trail, and the remark asks JLC not to
silently adjust the placement. The feeder-count question raised with this
order is open in §4.

## 3. Assembly options

- [ ] **Standard PCBA, top side only.** Economy is impossible for this board:
      ENIG and POFV each disable it, and U1 (ESP32-C6-MINI-1) + U5 (BMP581)
      are Standard-only parts (verified against a live quote 2026-07-18).
      All assembled parts are on F.Cu by construction (TPs/jumpers are
      copper-only, headers are DNP).
- [ ] Upload `out/fab/thermometer-c6-bom.csv` + `out/fab/thermometer-c6-cpl.csv`.
      **75 placements / 37 BOM lines.**
- [ ] **Confirm Parts Placement: Yes** (first order with this CPL — their
      engineer sends placement imagery for approval before assembly; ~+1 day).
- [ ] **PCBA Remark** — NOT free: filling it in adds an Advanced Options line
      `PCBA remark: "Quote after review"`, excluded from the displayed total
      and charged after their engineer reads it (observed 2026-07-20). Worth
      it for the U5 no-wash instruction. Paste:
      "U5 (BMP581) is a vented barometric pressure sensor — do not wash the
      board, no coating/ink over U5; standard reflow per Bosch guidelines is
      fine. Bake Y1/MSD parts at your discretion if floor life requires.
      J4 (C2856831 FPC-05FB-24PH20): mount with the contact-tail/cable-entry
      side toward the board edge. **Pin 1 is the filled silk dot beside the
      north end of the pad row** — there is no '1' glyph (the footprint marks
      it with an `fp_circle` at local (5.75, −2.6), directly beside pad 1 at
      local x +5.75).
      J3 (C165948 USB-C): please place J3 to the LAND PATTERN, not to the
      model body. In your placement preview the J3 model — body, solder tails
      and shell legs together — renders about 1.3mm off the pads and holes.
      J3 is an edge-launch part, so I do intend a small housing overhang past
      the north board edge; I make it 0.49mm, with every pad and shell slot
      still on the board, and I make the front shell slot 2.110mm from that
      edge per the HRO TYPE-C-31-M-12 drawing. If your DFM check reads any of
      that differently, please tell me before assembly rather than adjusting
      it."
- [ ] Expect one feeder-loading fee (~€2.75) per Extended BOM line — 16 lines
      as of 2026-07-18; only D3 (white C2290) and the 10k (C25744) have Basic
      same-footprint options, the rest have none (audited 2026-07-18). If JLC
      auto-substitutes the 10k with an Extended part (stock), re-match in the
      BOM review page to any in-stock **Basic** 10k 0402 — candidates
      C25744 (1%) / C60490 (1%) / C25531 (±5%; tolerance fine for all seven
      positions — pull-ups, gate series/bleed, and MCP73831 PROG where ±5%
      = 95–105mA). 2026-07-18 all three were out of JLC assembly stock at once
      and every in-stock 10k 0402 was Extended; **2026-07-20 C25744 is back in
      stock**, so the BOM's own part should go through as Basic and this
      contingency likely never fires. If it is gone again by order time, accept
      the auto-substitute (e.g. C174175) and eat the ~€2.75 feeder fee.
      Third-party part browsers show LCSC retail stock, not JLC assembly stock
      — **confirm C25744 in the BOM dialog itself**, which is the only view
      that reflects assembly availability.

## 4. Stock re-verification (before quoting)

Re-check LCSC/JLC stock — several parts run thin:

- [ ] U1 ESP32-C6-MINI-1-N4 **C5736265**
- [ ] Q3 Si1308EDL **C469327** (thin — fallback Si1304BDL clone **C7419947**)
- [ ] 10k **C25744** — back in stock 2026-07-20; re-confirm in the BOM dialog
      (alt **C60490**, then **C25531** ±5% Basic — see §3)
- [ ] **U5 BMP581 C5362283 — if out of stock, populate U6 BMP585 instead:**
      in `generator/circuit.py` set U5 `dnp=True` and U6/C26/C27 `dnp=False`
      (populate-exactly-one — both strap I2C 0x47), `make check`, commit, then
      re-run `make fab`. The BOM/CPL pick up the swap automatically.
      (In stock 2026-07-23: 6,563 pcs on JLC assembly, $2.35–3.03.)

Cost-reduction checks from the 2026-07-22 research (see README "Rev B
candidates → Cost reduction"; tiers/stock re-verified 2026-07-23 against
JLC's part API — the BOM dialog is still ground truth at order time):

- [ ] **Try matching D4–D6 MBR0530 → B5819W C8598** in the BOM dialog —
      confirmed Basic 2026-07-23 (621k stock, $0.029, SOD-123, Vf
      600mV@1A). One Extended feeder line saved *if* feeders are billed
      per Extended line (the feeder item below). Leakage/Vf deltas are fine for the
      gated booster.
- [x] **Tiers verified 2026-07-23 (JLC part API)**: C98192, C5204746,
      C469327 (stock 6,445 — thin), C2856831 all **Extended**. No Basic
      4.7µF ≥50V 0805 exists (the only Basic 4.7µF 0805 is 25V — too
      marginal for the ~22V EPD rails); nearest Basic alternative is
      **C440198** 10µF 50V X5R 0805 (2.4M stock) — a candidate line-kill
      needing booster re-validation, see README.
- [ ] **Feeder count and fee model, open since the 2026-07-20 order.** The
      Feeders Loading line billed 17 × ~€2.75 (€46.75, §8) while the BOM had
      16 Extended lines on 2026-07-18 and the BOM tab counted 15 Extended
      lines on 2026-07-20. JLC's live assembly-price page (updated
      2025-09-01) documents Standard PCBA at **$1.50 per unique line, Basic
      included** (Economic: $3 per Extended line, Basic free); 17 × €2.75
      matches the $3/Extended model, not the documented one. The "2025-12-19
      rate cut" was a third-party page edit, not a JLC announcement. Which
      model bills decides whether Basic swaps save feeder money at all. Ask
      support which 17 parts were counted (≈€2.75 per line), and check the
      model on the next itemised quote.
- [ ] **Quote POFV at qty 5/10/20** once, to learn whether the €44.07 is
      flat per order (amortises with volume) or scales — this decides how
      urgent the POFV-free rev B re-route is. Not documented anywhere
      public (2026-07-23: JLC's extra-charges article omits POFV; only
      documented fact is POFV is free on 6–20-layer, paid on 2/4-layer),
      so the quote calculator is the only oracle.
- [x] **X-Ray fee decoded 2026-07-23**: tiered per inspected piece
      ($1.57/pc at 1–10, $0.79 at 11–50, …), identical Economic/Standard;
      €11.46 ≈ 2 parts (U1 shield + U5 LGA) × 4 boards × $1.57. Mandatory
      for LGA/QFN/shield packages — not removable, but it scales with
      quantity rather than being a flat order fee.

## 5. FPC connector warning

- [ ] J4 must be **C2856831 (XUNPU FPC-05FB-24PH20, DUAL contact)**. The
      bottom-contact sibling **C2856805** looks identical in search results and
      does **NOT** work with the panel cable — never substitute.

## 6. Rotation/polarity verification (MANDATORY)

- [ ] In JLC's component-placement preview, walk `out/fab/rotation-checklist.md`
      row by row (22 orientation-critical parts; the 2026-07-20 copy is
      [`archive/order-2026-07-20/rotation-checklist.md`](archive/order-2026-07-20/rotation-checklist.md)). **The preview is ground
      truth** — the correction table in `generator/fab_cpl.py` is a first guess,
      and the SOT-23 family carries a known community-table conflict.
- [ ] On a mismatch: adjust the part's delta in `fab_cpl.py`, mark the entry
      `verified:`, re-run `make fab`, re-upload the CPL. If **all** parts are
      uniformly rotated or offset, suspect origin handling, not per-part deltas.
- [ ] Top-priority rows: **U5** (rotated LGA is invisible after reflow), **J4**
      pin 1, **U1** antenna WEST, and all FETs.
- [ ] Answer any JLC engineer polarity-confirmation email against the same
      checklist.

## 7. Archive after submitting

- [ ] Copy the exact uploaded zip + CPL + BOM + the ticked
      `rotation-checklist.md` into `archive/order-<YYYY-MM-DD>/`.
- [ ] Append a provenance entry to [`archive/README.md`](archive/README.md):
      commit hash, stamp, JLC order number, and the options chosen (ENIG /
      POFV / order-number position).
- [ ] Commit.

## 8. Quote history

Record every itemised quote here — earlier rounds were only ever remembered as
a bare total (~€205), which made "did that change?" unanswerable.

### 2026-07-20, bundle `87f5d93` — €204.94, qty 5 PCB / 4 assembled

| line | € | note |
|---|---|---|
| **PCB** | **64.49** | |
| — Via Covering (POFV) | 44.07 | the single largest cost on the board |
| — Surface Finish (ENIG) | 14.84 | |
| — Via Plating Method | 2.92 | |
| — Special Offer | 1.75 | |
| — Confirm Production file | 0.91 | |
| **Standard PCBA** | **140.46** | |
| — Components (35 items) | 49.62 | 37 BOM lines, 35 unique parts — see below |
| — Feeders Loading | 46.75 | **= 17 × €2.75 exactly**; the feeder question is open in §4 |
| — Setup Fee | 22.32 | |
| — X-Ray Inspection | 11.46 | mandatory (U1 shield + U5 LGA); tiered per piece ≈ 2 × 4 × $1.57 |
| — Stencil | 7.17 | |
| — SMT Assembly | 2.32 | |
| — Packaging | 0.43 | |
| — Confirm Parts Placement | 0.39 | wanted — see §3 |
| — Panel / Large Size | 0.00 | |
| **Advanced** | | |
| — Depanel + edge rail | 2.58 | opt-in; advanced options add a build day |
| Build time | 0.00 | PCB 3d, assembly 3–4d (2–3d would be +€43.01) |

Coupon €17.46 applied → €198.94. Weight 527.10g (5 boards + edge rails; JLC
grows the panel to 70×71mm because Standard PCBA needs ≥70mm a side).

**Shipping: the quoted estimate is a lie for this order.** The quote and cart
pages advertise "Global Standard Direct Line" (€1.31 / €9.72), but at
checkout that line is restricted to orders **under $150** — this order is
~€199, so it is not selectable and the real carrier costs more. Budget for
the actual checkout options, not the estimate. Splitting the order to get
under the cap is not worth it: the €22.32 PCBA setup fee is per-order.

**The 35-vs-37 gap is benign — resolved 2026-07-20 in the BOM tab.** JLC
reported "37 parts detected / 37 parts confirmed"; it bills 35 because two
pairs of BOM lines share one LCSC part and get merged: R18/R19/R22/R23/R5
with R20/R21 (both **C25741**), and SW1 with SW2 (both **C318884**). The ⚠
icons on those rows are merge notices, not problems. Checked the one that
would have mattered: R20/R21 are the VBAT_ADC divider and are spec'd 1% —
C25741 is `0402WGF1003TCE`, whose `F` code IS ±1%, so the merge does not
quietly downgrade battery-sense accuracy.

Deltas worth watching next round: the feeder count (§4), and whether X-Ray
and depanel are optional.

Settled deliberately 2026-07-20, do not "correct" these: **white** solder
mask (not green) and **lead-free / high-temp** solder paste.

### Import charges — budget them, they are not on JLC's invoice

JLC invoice (2026-07-27): merchandise €209.27 (bare PCB €13.25 + 4×
assembled €49.01) + shipping €20.12 (DHL Express Worldwide, CPT) − coupon
€17.46 = **€211.93 paid**. DHL door bill: **€62.00** = €42.00 TVA (20% of
the €211.93 invoice total — checks exactly) + €20.00 clearance fee ("frais
additionnels de dédouanement", €16.67 + its own TVA). Actual customs duty:
€0 — EU tariff on populated PCBs is zero, so the entire door charge is VAT
plus the courier's fixed fee. **Landed: €273.93 ≈ €68.50 per assembled
board.**

Rule for future orders: anything over €150 gets import VAT collected by the
courier (20% of goods + shipping) plus a ~€15–20 disbursement fee — add
~22–25% to the checkout total to get the landed cost. Sub-€150 orders with
IOSS (LCSC/DigiKey style) prepay VAT at checkout and owe nothing at the
door, which is why small part orders never showed this. Splitting an order
under €150 to dodge the fee still loses: the €22.32 PCBA setup fee is
per-order (see shipping note above).
