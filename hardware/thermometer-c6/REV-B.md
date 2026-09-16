# Rev B candidates — proposal register

Proposals for a rev B of thermometer-c6. **None is ordered**; rev A is the
board in service. A row's observed cell is filled when a measurement lands,
with a link to the logbook entry that holds it. The supporting research per
item follows the table, as researched on the dates given.

| Candidate | Gate | Expected | Observed | Date |
|---|---|---|---|---|
| [Panel readback (SDO)](#panel-readback-sdo) | probe a T81 with `display_probe_readback()` behind `EPD_PROBE` | per-controller; no board change buys anything | UC8151 answers on the wiring as built (board 2, GDEY0213M21, 2026-08-05); SSD2677 untested; the LUT consequence is fixed in firmware | 2026-08-11 |
| [Board shrink east, 48×35 → 47×35 or further](#board-shrink-east-4835--4735-or-further) | a placement pass that gives Q1 somewhere to go | no fab saving, 1680 → 1645mm² is the same JLC tier | H1's screw-head keepout would overlap Q1's courtyard by 0.806mm; study in `out/east-shave/` | — |
| [Q1 to H1 screw-head keepout](#q1-to-h1-screw-head-keepout) | rev B placement pass | — | 0.105mm clearance on rev A | — |
| [USB connector-segment symmetry](#usb-connector-segment-symmetry) | only if the path ever carries High Speed | 1.90mm of skew removed by swapping USBLC6 channels | +2.31mm (B-row mated) / +5.21mm (A-row) skew, irrelevant at 12 Mbps | — |
| [Sensor placement against heat sources](#sensor-placement-against-heat-sources) | a clean equilibrium delta per mode, `BRINGUP.md` Phase 3 | close to a wash thermally (calculated, none measured) | unmeasured; board 1's 33.9°C vs 29.8°C is not evidence | — |
| [GND reference under the USB path](#gnd-reference-under-the-usb-path) | — | acceptable at full speed | pour coverage 16.8% / 0.0% / 2.4% / 0.0% on the four USB nets vs 28%/40% board-wide | — |
| [Key presses on silkscreen](#key-presses-on-silkscreen) | — | recovery obvious from the silk | — | — |
| [POFV removal by re-route](#pofv-removal-by-re-route) | confirm POFV is a flat charge vs qty (quote at 5/10/20) | −€44.07/order, the single largest line | 81 vias in solderable pads, 26 hard-boxed | 2026-07-23 |
| [Panel-lock BOM collapse](#panel-lock-bom-collapse) | panel choice final | −€3–9/order | no sag on the universal config under LUT 235, board 2 + T81 ([notes.md](../../docs/notes.md#boost-rails-under-the-worst-case-waveform-board-2--t81-2026-08-11)) | 2026-08-11 |
| [MBR0530 → B5819W diode swap](#mbr0530--b5819w-diode-swap) | feeder question resolved (`ORDERING.md` §3/§4); the saving assumes per-Extended-line feeder billing | −~€2.75/order | B5819W C8598 Basic tier, 621k stock, $0.029 | 2026-07-23 |
| [C98192 → C440198 capacitor swap](#c98192--c440198-capacitor-swap) | booster re-validation against a bench board | −~€2.75/order, same feeder caveat as the diode swap | C440198 10µF 50V X5R 0805 Basic, 2.4M stock | 2026-07-23 |
| [Production-copper trim](#production-copper-trim) | after the rev A first-article campaign | −~€1–6/order, mainly routing room | — | — |
| [Order quantity](#order-quantity) | none | qty 15–20 takes unit cost from ~€51 to ~€20–25 | ~€78/order fixed | 2026-07-22 |
| [32k load caps](#32k-load-caps) | load-cap bench test on a retired board (`BRINGUP.md`) | re-centre the fleet's shared slow offset | three FC-135 rates all negative, 2026-08-23 ([clock-drift.md](../../docs/clock-drift.md#fc-135-first-record-bias-and-load-cap-hypothesis-2026-08-23)) | 2026-08-23 |

## Candidates


Deliberately NOT taken for rev A — each is real but none justifies a respin
of a board that is otherwise order-ready.

### Panel readback (SDO)

Whether the panel can answer the host at all depends on its controller, not on
this board, so there is no single answer to carry forward. **UC8151 works on the
wiring as built**: probed 2026-08-05 on board 2 with a GDEY0213M21, `0x70` →
`01 0e`, `0x71` → `13 13`, `0x40` → `d2 00`, each byte identical whether the
input was pulled up or down (i.e. actively driven), while foreign SSD168x
commands floated — that contrast is the control. **SSD2677 (the T81) is
untested, and no longer "unlikely".** An earlier note here said it could not
reply because the FPC carries no SDO. That was wrong: `SSD1677.pdf` names
`SDI`/`SDO` as separate **chip** pins in 4-wire mode, but the T81 module bonds a
single `SDA` to FPC pin 14 — exactly like every other panel here, none of which
exposes an SDO either. Its module datasheet calls that pin an input and
documents no read procedure, which was equally true of the M21 before the M21
answered. **Probe a T81 before concluding anything.** **It has never been asked,
only never listened to.** `_Init_Full` reads the controller temperature to pick
a waveform LUT and gets 0, but GxEPD2's `_readData()` samples the line in
software and works only in bit-banged mode, and this build runs hardware SPI —
so no wiring conclusion follows from the 0. **This stopped being a board
question on 2026-08-11.** The LUT consequence is fixed in firmware (upstream's
guarded 20–30 °C fallback, then the BMP581 value fed in directly), and feeding a
calibrated ambient reading beats any readback of a self-heating die — so neither
3-wire mode (a 9-bit protocol GxEPD2's 4-wire path does not implement) nor an
SDO on the FPC buys anything a rev B should pay for. A probe is now worth
running for the cross-check alone: `display_probe_readback()` behind
`EPD_PROBE`. **What is readable is narrow, and per-controller.** On the UC8151
only three registers answer — `0x70` REV, `0x71` FLG, `0x40` temperature — and
they answer identically before and after GxEPD2's init. `0x61` TRES and `0x00`
PSR **float**, so resolution cannot be read back: the datasheet calls TRES a
host-set override anyway, and probing before init confirmed it is not merely
being overwritten. Resolution would in any case only ever **falsify** a match,
never confirm one — two different 200x200 panels agree on it. The one
panel-intrinsic value on offer is `0x70`'s `LUT_REV`, sourced from OTP address
`0x001`, since a waveform LUT is tuned to its glass. Caveat before trusting it
as an ID: our bytes (`01 0e`) do not match the datasheet's documented `CHIP_REV`
of `1101b`, so the framing (a dummy first byte on OTP reads, or bit alignment)
is unresolved — the values are stable and repeatable, so they serve as an opaque
fingerprint, but should not be reported as "the chip revision" until that is
settled. And nothing here transfers: an SSD168x command set floats entirely on a
UC8151, so every panel family needs its own probe table.

### Board shrink east, 48×35 → 47×35 or further

J4's mouth is at x46.40, already 1.60mm inboard of the east edge, and there is
no copper east of x46.0 (easternmost feature: the GND via at (45.60, 28.25)).
The binding constraint on the 48.0 edge is **H1**, not J4: a ⌀2.2 hole at (45.8,
2.2) with the R2.2 corner arc concentric with it, giving a uniform 1.100mm ring
of FR4 around the corner. Shrinking means moving H1 west with the edge and
re-centring both east corner arcs — the FR4 ring survives at 1.100mm, but H1's
⌀4.993 screw-head keepout then overlaps Q1's courtyard by 0.806mm. No fab saving
(1680 → 1645mm² is the same JLC tier), so this is only worth doing as part of a
placement pass that gives Q1 somewhere to go. Study, scripts and renders:
`out/east-shave/`.

### Q1 to H1 screw-head keepout

Q1 clears H1's ⌀4.993 screw-head keepout by only 0.105mm on the
current board (nearest Q1 courtyard corner (43.345, 3.062) is 2.602mm from
H1's centre). Independent of any shrink; worth a deliberate look in a rev B
placement pass.

### USB connector-segment symmetry

`USB_D+`/`USB_D-` (U3→U1) are matched to 0.024mm, but the connector segment is
not: D+ is daisy-chained *through* B6 to A6 (a series node, not a tap) while D-
gets a balanced tee, so end-to-end skew is +2.31mm (B-row mated) or +5.21mm
(A-row). 1.90mm of that is pure USBLC6 pinout — pins 1 and 3 sit 1.90mm apart on
the same SOT-23-6 edge — and would vanish for free by swapping which (symmetric)
channel carries which polarity. Irrelevant at the C6's 12 Mbps full speed (~31ps
against an 83,333ps bit period, 4–20ns edges); it would start to matter only if
this path ever carried High Speed.

### Sensor placement against heat sources

Edge-to-edge courtyard gaps:

| heat source | → U5 (fitted) | → U6 (DNP alt) |
|---|---|---|
| U1 ESP32-C6 module | 2.25mm | 4.25mm |
| U2 RT9080 LDO | 4.90mm | 3.00mm |
| U4 MCP73831 charger | 36.8mm | 38.0mm |

Populating U6 instead of U5 gains 2.0mm from the module and gives back 1.9mm
to the LDO, so as a thermal move it is close to a wash — the obvious "put the
default sensor at the far site" is not obviously an improvement.

Which source matters depends on the mode, and duty cycle dominates the
arithmetic (all figures below are calculated, none measured):
- **Charging**: (5.0−3.7)V × 100mA ≈ **130mW continuous** at U4 for the whole
  CC phase — much the largest steady source, and 37mm from both sites, so it
  reaches the die as whole-board bulk warming through the pour rather than as
  a local gradient. **Sensor placement cannot fix this one**; a thermal moat,
  a lower charge current, or suppressing/flagging readings while charging are
  the levers.
- **Deployed on battery**: the CPU is awake ~1s per wake, so ~100mW while
  awake time-averages to single-digit mW, and the LDO is sub-mW. Nothing here
  needs fixing — this is the mode the device actually lives in.
- **Parked on USB** (the new service window, `docs` in `BRINGUP.md` Phase 3):
  the CPU is continuously awake, ~100mW at 2.25mm, plus ~50mW at the LDO
  (1.7V drop at ~30mA) 3–5mm away. This is the mode where local placement
  would actually pay, and it is a bench mode, not a deployment one.

The no-pour keep-outs under both sensors already remove the plane coupling
(Bosch thermal-fidelity guidance) but buy no distance.

**There is no usable measurement yet.** Board 1's 33.9°C-vs-29.8°C is not
evidence: it mixes bench sun, USB self-heat and the operator's fingers on the
board (it decayed afterwards). Get a clean equilibrium delta per mode before
anyone moves a footprint — `BRINGUP.md` Phase 3.

If placement is revisited, the target is a site far from **both** U1 and U2 —
the south/south-west edge — not U6's slot. Note a literal U5/U6 coordinate
swap is infeasible anyway: U6's courtyard is 3.5mm square against U5's 2.2mm,
and the northern slot has 0.45mm of headroom with the antenna keep-out and C12
boxing it in, so it wants a re-flow of the sensor picket (U5/U6 +
C12/C13/C26/C27), which is also what would let both move away from the LDO.
Rev A can still bound the U1-proximity term on its own: the sites are
populate-exactly-one and the driver reads the chip ID (0x50/0x51), so building
one of boards 2–4 with U6 gives an A/B on the same rig (confounded by the
different package and die-to-pad path). Needs a BMP585 (C18184976) in the next
order.

### GND reference under the USB path

Opposite-layer pour coverage is 16.8% / 0.0% / 2.4% / 0.0% across the four USB
nets against 28%/40% board-wide — the 0.5mm zone clearance starves the pour out
in the dense x18–27, y6.7–15 window. The long D+ vertical crosses six foreign
nets on B.Cu in 4.9mm and the two western signal vias have no GND stitch within
4mm. Acceptable at full speed and the EPD boost switching nodes are not among
the crossings, but it is the condition the path runs in.

### Key presses on silkscreen

It would make it obvious how to recover. Especially: download mode, restarting
firmware, as those are not software defined. The shutdown sequence would be
interesting as well but might not be a good idea as it could change.

### 32k load caps

Filed 2026-08-23 from the FC-135 harvest: the three rates are all negative,
which a symmetric initial tolerance would not produce. The bench test (a few
pF across one crystal leg on a retired board, re-measure the rate) is a
[`BRINGUP.md`](BRINGUP.md) item, and the order-of-magnitude pulling argument
is in
[clock-drift.md](../../docs/clock-drift.md#fc-135-first-record-bias-and-load-cap-hypothesis-2026-08-23).
The trim is conditional on that test confirming the slope.

## Cost reduction (researched 2026-07-22)


Baseline: the €204.94 qty 5 PCB / 4 assembled itemised quote in ORDERING.md §8.
The order landed at €273.93 (€211.93 JLC invoice 2026-07-27 + €62.00 DHL) ≈
€68.50/assembled board — breakdown in ORDERING.md; the per-unit analysis below
reasons from the quote. Three structural facts frame everything: **Economy PCBA
is unreachable regardless of PCB options** (U1 and U5 are Standard-PCBA-only
parts, both locked; Economy is also single-sided-placement, ≤50pcs), **X-Ray is
mandatory** for U5's LGA and U1's shield (tiered per inspected piece — $1.57/pc
at 1–10; the €11.46 ≈ 2 parts × 4 boards — so it scales with quantity, it is not
a flat order fee), and **no wireless SoC or environmental sensor exists in the
JLC Basic tier at all** (verified 2026-07-23: Basic-filtered library probes for
ESP32/ESP8266/nRF/BL602/ W800/CH57x/CC25xx/RTL87xx all return zero) — so
feeder-fee optimisation is small-bore and the real levers are POFV, quantity,
and BOM-line count. Tier/stock facts below re-verified 2026-07-23 against JLC's
own part API (`getComponentDetail`); fee-policy facts against jlcpcb.com's live
assembly-price page. The order dialog remains ground truth at order time.

### POFV removal by re-route

Not a touch-up: a full via audit of the committed board found **81 vias in
solderable pads** (independently reproduced 2026-07-23 with a pcbnew
script: 84 via centres in mask-open SMD pads, 81 excluding the JP2/3/5
copper-jumper pads) — via-in-pad is the board's core 2-layer escape
strategy.
~50 have a legal dog-bone spot against today's copper (FPC-east fanout
column, central EPD-driver discretes, all GND stitches); **26 are
hard-boxed** with no clear spot within 1mm — dominated by 12 ESP32-C6 QFN
pins (0.4mm pads narrower than the 0.6mm via), the 32k crystal pair, the
sensor pins, and the USB-C VBUS/CC joints. J4 (0.5mm FPC) and U5 (LGA)
are already via-in-pad-free, so nothing is geometrically impossible.
Opportunity cost: days — grow the outline (free up to JLC's 100×100mm
tier), re-place the west/QFN cluster, re-route essentially from scratch,
full-severity DRC again, and a fresh first-article risk. Best bundled
with the Q1/H1 placement pass above and the production-copper trim below
(the freed bench-pad corridors are exactly where the dog-bones must go).
Before committing to it, confirm POFV is a flat charge vs qty (quote at
5/10/20) — if flat, large orders amortise it and weaken the case. The
scaling is not documented anywhere public (checked 2026-07-23: JLC's
extra-charges article doesn't list POFV; the only official pricing fact
is that POFV is free on 6–20-layer boards, paid on 2/4-layer), so the
quote calculator is the only oracle.

### Panel-lock BOM collapse

Locking the panel family to the proven 10µH/0.47Ω config deletes L2 (47µH,
Extended), R15 (2.2Ω) and R16 (3Ω) plus their placements; JP2–JP6 are
copper-only and can stay. Opportunity cost: the board loses the
GDEH0576T81-datasheet booster option (47µH + 2.2Ω RESE) and the 3Ω SSD16xx leg —
fine iff the panel choice is final; the copper jumpers keep a hand-solder escape
hatch. **The evidence this was waiting on landed 2026-08-11: no sag.** PREVGH
(C5) +20.031 V and PREVGL (C11) −19.380 V, means repeating to 20 mV and 73 mV
across refreshes, both flat for the whole ~3.03 s drive of the **LUT 235
waveform** — the heaviest the T81 can be given — on the factory JP2/JP5 bridges
with nothing reworked. A pump short of the load would decay across that window;
neither rail does. With GDEM0154I61, GDEY0213M21 and now the T81 all working on
the universal config, the datasheet pair is margin nothing has needed. Numbers
and the two limits (measured ahead of the panel's internal regulation; 10 Hz
sees nothing under ~100 ms) in `../../docs/notes.md`.

### MBR0530 → B5819W diode swap

Same
SOD-123 package, 40V/1A vs 30V/0.5A. Verified 2026-07-23 via the JLC
part API: **Basic tier, 621k stock, $0.029** (MBR0530 C5204746 confirmed
Extended). Vf 600mV@1A vs 500mV@500mA costs a hair of refresh
efficiency; reverse leakage is irrelevant (the whole booster hangs off
gated EPD_VCC). Caveat: the −€2.75 assumes the per-Extended-line feeder
billing the 2026-07-20 quote exhibited — under JLC's *documented*
Standard-PCBA policy ($1.50 × every unique line, Basic included) the
swap is feeder-neutral and saves only pennies of part cost. Resolve the
feeder question (ORDERING.md §3/§4) before counting this saving.

### C98192 → C440198 capacitor swap

C98192 (4.7µF/50V, 9 placements, one Extended line) → C440198 is a
candidate Basic swap: −~€2.75/order, with the same feeder caveat as the diode
swap. There is no Basic 4.7µF ≥50V 0805 (verified 2026-07-23; the only Basic 4.7µF
0805 is 25V), but **C440198 10µF 50V X5R 0805 is Basic** with 2.4M stock.
Doubling the pump/reservoir caps (C16–C24) and the VBUS-side C5/C6 needs booster
re-validation (startup surge, pump timing) — try only with a bench board to
compare against, and mind X5R DC-bias derating at the ~22V rails is similar for
both parts.

### Production-copper trim

The board already carries its debug features as DNP/copper-only (J5, J2, JP1–6,
all TPs, R9, U6), so they cost nothing at assembly. What a production variant
can still cut: SW1/SW2 → tweezer-shortable pads (keeps the unbrick path —
USB-Serial-JTAG download works but the device deep-sleeps ~99% of the time, so a
physical BOOT-at-power-on path is worth keeping in some form) and D3 (status is
the EPD's job). Keep D1: CHG_STAT reaches no GPIO, so it is the only charge
indication. The real value is deleting TP/J5/J2/U6 copper in the same pass — TP7
alone pinches the B.Cu channel south of the booster to a 0.30mm slot, and the
bench pads impose 2.1mm HV keepout walls — which is exactly the room the POFV
dog-bones need. Opportunity cost: the PPK2 bench procedures above stop working
on that variant; only strip after the rev-A first-article campaign is done.

### Order quantity

~€78/order is fixed (setup 22.32, feeders 46.75, stencil 7.17, confirm
fees 1.30); X-Ray (€11.46) is tiered per inspected piece so it shrinks
per-board with volume but never disappears. At qty 4 assembled that is
~€20–23/board of pure overhead. Qty 15–20 takes unit cost from ~€51 to
~€20–25 with the design untouched (modulo how POFV scales — see above).

Ruled out, with reasons (don't re-research):

- **SoC alternatives — U1 stays.** Requirements bar (docs/notes.md): hold
  the 14–16µA system deep-sleep floor, sample I2C every 60s in deep sleep
  at ~50nA average without booting the HP core (LP core), 32.768kHz XTAL,
  WiFi. ESP32-C3/C2/ESP8685/ESP8266/BL602/W800 all fail the LP-sampling
  bar (no LP/ULP coprocessor; ESP8266 also ~20µA floor) and save ≤€1.
  Nordic nRF52x has best-in-class sleep and a CPU-off TWIM sampling path
  but is BLE-only — fails WiFi outright. Bare ESP32-C6FH4 saves ~$0.5 and
  costs antenna design + modular RF certification. No wireless part is
  Basic tier, so there is no feeder-fee escape either.
- **Sensor alternatives — U5 stays.** BMP581 is ~$1.44 at LCSC ($2.35–3.03
  through JLC assembly) — already the cheapest pressure-capable part that
  passes the power bar (~0.5µA standby, ~3µC/forced reading). BMP390L costs *more* (~$5) despite the
  existing driver; BMP280 saves pennies and is equally Standard-only.
  SHT40 is the standout if pressure were expendable (80nA, ~2.4µC, ±0.2°C,
  ~$1.3) but its Economy-capability is moot (U1 forces Standard) and it
  drops pressure. AHT20/21 fail per-reading energy (~80ms conversions);
  MCP9808 (~50µC/reading at 0.1°C res), STTS22H (1.75µA standby), LM75B
  (±2°C) all fail the bars. An NTC divider (~$0.01, GPIO-gated → zero
  standby, like the battery divider) passes the power bars trivially but
  is ±0.5–1°C uncalibrated (±0.2–0.3°C with single-point cal), needs C6
  SAR ADC characterisation to reach 0.1°C resolution, and drops pressure.
- **ENIG stays** (€14.84): the locked 0.5mm-pitch LGA and FPC sit at JLC's
  0.20mm HASL clearance floor, and dropping it cannot unlock Economy
  anyway. **X-Ray stays**: mandatory for LGA. **D1, USBLC6, Q6, Y1 stay**:
  charge indication, ESD, reverse-battery survival and timekeeping are
  functionality, and each saves pennies at best.

Net: cheap wins (panel lock + diode swap + production trim) ≈ €15–25/order
with rev-A-class effort; the POFV rev B adds ~€44/order more but is a real
re-layout; quantity halves unit cost on its own.
