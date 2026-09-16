# thermometer-c6 — custom ultra-low-power e-paper thermometer board

Custom PCB replacing the XIAO-C6/FireBeetle dev-board rigs. ESP32-C6-MINI-1 +
BMP581 + universal 24-pin EPD interface with on-board gated booster, USB-C
charging, LDO power tree. Design driven by the PPK2 measurement campaign in
[`docs/notes.md`](../../docs/notes.md) (repo root).

![Thermometer C6 rev A board & GDEM0154I61 (2026)](../../docs/photos/revA-GDEM0154I61.jpg)

## Docs in this directory

| Doc | What it is | Status |
|---|---|---|
| [BRINGUP.md](BRINGUP.md) | Bench queue and per-board state for rev A | live |
| [ORDERING.md](ORDERING.md) | Fab and assembly options, the JLCPCB order walk, quote history | procedure |
| [REV-B.md](REV-B.md) | Rev B proposal register: candidate, gate, expected, observed | proposal |
| [HAND-ROUTING.md](HAND-ROUTING.md) | Copper edits in the KiCad GUI, harvested back into the generator | procedure |
| [EE-PRIMER.md](EE-PRIMER.md) | Field guide to the schematic's symbols and idioms, by designator | background |
| [SCHEMATIC-VERIFICATION.md](SCHEMATIC-VERIFICATION.md) | Rev A pre-order schematic sign-off, 2026-07-20 | record |
| [REVIEW-KICAD-HAPPY.md](REVIEW-KICAD-HAPPY.md) | kicad-happy design review runs, 2026-07-17 and 2026-07-20 | record |
| [LAYOUT-PLAN.md](LAYOUT-PLAN.md) | How the layout was planned and decided, up to the 2026-07-20 order | historical |
| [ROUTER-NOTES.md](ROUTER-NOTES.md) | The retired greedy A* router | historical |
| [PATHFINDER-NOTES.md](PATHFINDER-NOTES.md) | Negotiated-congestion router experiment, not adopted | historical |
| [archive/](archive/README.md) | Hand-routed snapshots, the 2026-07-20 order as uploaded, worktree patches | record |
| [archive/bringup-rev-a-first-article.md](archive/bringup-rev-a-first-article.md) | Rev A first article on board 1, Phases 0–2 and the Phase 3 items closed since | record |
| [../datasheets/](../datasheets/README.md) | Panel and carrier vendor PDFs, panel readback findings | reference |

**Status: rev A built and working.** Ordered 2026-07-20
([`archive/order-2026-07-20/`](archive/order-2026-07-20/); landed €273.93 ≈
€68.50/assembled board, breakdown in [`ORDERING.md`](ORDERING.md)). Board 1
passed bring-up Phases 0–2 on 2026-07-29 ([`BRINGUP.md`](BRINGUP.md)): first
render, LP-core survival, and a measured 18.3µA @ 4.2V deployment-path sleep
floor over a full field interval (docs/notes.md 2026-07-29) — vs 21.7µA at
the same 4.2V on the XIAO buck rig, validating the LDO tree. **Phase 3 is under
way on board 2, not board 1**: the GDEH0576T81 panels arrived 2026-08-11 and
board 2 took one plus a battery, so the phase is no longer gated on board 1
leaving its soak (still running since 2026-07-31; harvest before resetting it).
Closed on board 2 that day: the deployment configuration's power figures
(19.05µA floor, 36.77mC wake+refresh `@4V2 bat`), the boost rails under the
heaviest waveform the panel can be given (no sag — this is the evidence the
rev B bridge deletion was waiting on), the VBAT_ADC point (−24mV at 4.2V, 2mV
from board 1), the battery-floor sweep, and the WiFi resync charges. Board 2
went straight to flash on the strength of board 1's pass, worked first time,
and is both the bench board and now the Phase 3 vehicle; boards 3–4 are still
in the bag. The board is 48×35mm
2-layer, hand-routed, DRC-clean at full severity; fab export is `make fab`
(gerbers/drill + CPL/BOM zip, git-hash+date stamped, gated by
`verify/check_fab.py`); pre-order schematic sign-off (requirements proven
against primary sources, findings + dispositions):
[`SCHEMATIC-VERIFICATION.md`](SCHEMATIC-VERIFICATION.md).

## Why these choices (measurement rationale)

| Decision | Measurement behind it |
|---|---|
| LDO (not buck) 3.3V rail | XIAO's SGM6029C buck: razor-sharp dropout cliff at 3.545V → 0.5–0.9A brownout storms; forces 3.70V firmware shutdown, wasting ~12–15% of pack (notes.md 2026-07-05) |
| P-FET-gated EPD booster | DESPI-C02 leaks ~534µA with panel asleep; FDN340P gate mod → ~18µA (notes.md) |
| Switched 100k/100k battery divider | Always-on 200k divider ≈ 10µA (~⅔ of the sleep floor); 1M/1M biases the C6 SAR ADC low (~300ns sample window) (wiring.md) |
| High-side divider switch | Low-side switch leaves the sense node at VBAT through the top 100k → pin ESD diode clamps into 3V3 above ~3.7V (~5µA at 4.2V) |
| Load-sharing USB path | Without it, no-battery USB operation is limited to the 100mA charge current — EPD refresh peaks at ~465mA |
| Reverse-battery P-FET (Q6) | JST vs Adafruit pigtail polarity is a real supply-chain trap; MCP73831 abs-max is −0.3V — one AO3401A makes it survivable |
| EPD gate soft-start (R24/C28) | GPIO14 slamming Q2 on charge-shares 10µF against the rail faster than the LDO loop — ~100µs ramp kills the brownout risk |
| VBUS sense (R22/R23 → GPIO4) | Firmware needs to know USB is present: VBAT_ADC reads the charger CV node while charging, and SoC logic must ignore it; zero draw with USB absent |
| Jumper-selected inductor (JP5/JP6) | 10µH proven on all panels; 47µH per the GDEH0576T81 datasheet (with 2.2Ω RESE) — jumpers sit on the switch-node side so the unselected coil idles on the DC rail |
| 32.768kHz crystal | C6 on internal RC runs hours fast over weeks (memory: project_c6_clock_drift) |

## Reference transcription: DESPI-C02 V1.0 (Good Display, 2018-07-06)

Transcribed from `hardware/datasheets/DESPI-C02_SCH V1.0.pdf` (visual + embedded netlist),
2026-07-07. This is the booster we replicate (with EPD_VCC gating added).

### 24-pin 0.5mm FPC panel pinout (P1, "FPC24(0.5MM)")

| Pin | Name | DESPI connection | Pin | Name | DESPI connection |
|---|---|---|---|---|---|
| 1 | NC | — | 13 | SCLK | host SPI SCK |
| 2 | GDR | Q1 gate + R1 10k→GND | 14 | SDI | host SPI MOSI |
| 3 | RESE | Q1 source + Rsense→GND | 15 | VDDIO | 3.3V |
| 4 | VGL | C1 4.7µF/25V→GND | 16 | VCI | 3.3V |
| 5 | VGH | C2 4.7µF/25V→GND | 17 | VSS | GND |
| 6 | TSCL | — (touch variant only) | 18 | VDD | C7 1µF/50V→GND |
| 7 | TSDA | — (touch variant only) | 19 | VPP | C8 1µF/50V→GND |
| 8 | BS | R4 3Ω→GND (= tied low, 4-wire SPI) | 20 | VSH | C9 4.7µF/25V→GND |
| 9 | BUSY | host | 21 | PREVGH | C5 4.7µF/25V→GND + D3 cathode |
| 10 | RES | host + R5 10k→3.3V pull-up | 22 | VSL | C10 4.7µF/25V→GND |
| 11 | D/C | host | 23 | PREVGL | C11 4.7µF/25V→GND + D1 anode |
| 12 | CS | host | 24 | VCOM | C12 1µF/50V→GND |

### Booster topology (all diodes MBR0530; orientation by function, not pin #)

- L1 10µH/1A: 3.3V → SW node
- Q1 Si1308EDL N-FET: gate=GDR (R1 10k bleed to GND), drain=SW, source=RESE
- RESE → Rsense → GND. DESPI: slide switch selects R3 0.47Ω or R2 3Ω.
  **This board: three parallel legs, each Rsense in series with a solder
  jumper: 0.47Ω (default-bridged) / 2.2Ω / 3Ω.**
- D3: anode=SW, cathode=PREVGH (boost rectifier)
- Negative charge pump: SW → C3 4.7µF/25V → X node; D2 anode=X, cathode=GND;
  D1 anode=PREVGL, cathode=X
- 3.3V rail bulk: C4 4.7µF/25V. (On this board the whole block hangs off the
  gated EPD_VCC rail, and the RES pull-up goes to EPD_VCC — never 3V3.)
- There are **no** PREVGH↔PREVGL/VCOM bridge caps in the real reference
  (the abandoned draft in `hardware/kicad/` invented them).

## ESP32-C6 pin map

| GPIO | Function | Notes |
|---|---|---|
| 0 / 1 | XTAL_32K_P / N | FC-135 32.768kHz + 20pF; R9 10M bias DNP — the C6's 32k oscillator amplifier runs at very low gm, so startup margin depends on crystal ESR spread (≤70kΩ allowed, rises when cold) and stray C; the parallel bias resistor (Espressif HDG checklist) gives the inverter a DC feedback path if a given board/batch won't start |
| 2 | VBAT_ADC (ADC1_CH2) | sense node of switched divider; 0V when divider off |
| 3 | VDIV_EN | 100k pull-down → divider hard-off in deep sleep |
| 4 | VBUS_SENSE (100k/100k from VBUS) | USB-presence detect; divider is dead (0V, zero drain) with USB unplugged |
| 5 | spare → J5 debug header | strap-adjacent (SDIO clock-edge only at default eFuses) — keep high-Z |
| 6 / 7 | LP I2C SDA / SCL | fixed by silicon; BMP581; 4.7k pull-ups to 3V3 |
| 8 | spare → J5 | STRAP: must be free to pull high for download boot — header only |
| 9 | BOOT button | strap, its intended use; 10k pull-up |
| 12 / 13 | USB D− / D+ | native USB-Serial-JTAG via USBLC6-2SC6 |
| 14 | EPD_PWR_EN (P-FET gate) | chosen because it is NOT in the SDIO strap group (GPIO18–23 can toggle during early boot, esp-idf #11975); 10k pull-up → panel off at reset/sleep |
| 15 | Status LED | safe: JTAG_SEL strap ignored at default eFuses |
| 16 / 17 | UART0 TX / RX → J5 | module pins TXD0/RXD0 |
| 18–21 | EPD MOSI/SCK/CS/DC | SDIO-group boot toggles drive an unpowered panel — harmless |
| 22 | EPD RST | 10k pull-up to **EPD_VCC** (gated) |
| 23 | EPD BUSY (input) | |

## Debug header J5 (2×5, DNP — GND-first, no VBAT)

The silk carries only a `DBG` marker (no room for a per-pin legend at ≥0.8mm),
so the pinout lives here. Standard 2×5 numbering, pin 1 = the marked corner:

| Pin | Signal | | Pin | Signal |
|---|---|---|---|---|
| 1 | GND | | 2 | +3V3 |
| 3 | EN (reset) | | 4 | DBG_TX (UART0 TXD0, GPIO16) |
| 5 | DBG_RX (UART0 RXD0, GPIO17) | | 6 | VBUS_SENSE (GPIO4) |
| 7 | DBG_IO5 (spare GPIO5) | | 8 | DBG_IO8 (spare GPIO8, strap) |
| 9 | GND | | 10 | GND |

DNP by default — solder a header only if you need wired debug/UART. **BOOT is
not on J5** (it's the SW2 button only); only EN is exposed here.

## Charging rule (product decision, 2026-07-07)

**Charge indoors only (0–45°C).** The MCP73831 has no thermistor input;
charging LiPo below 0°C plates lithium. The board carries this on back silk
(`CHARGE INDOORS 0-45°C`). Related: don't leave USB permanently attached — the
charger float-cycles the cell between ~3.95V and 4.2V indefinitely.
Firmware should also refuse to advertise "charge OK" below 0°C using the
BMP58x temperature (belt and braces; it cannot stop the charger).

## Inductor solder jumpers (JP5/JP6) — bridge exactly one

| Bridge | L | Pair with |
|---|---|---|
| JP5 (default) | L1 10µH | RESE 0.47Ω or 3Ω — the proven DESPI-C02 config for all six panels |
| JP6 | L2 47µH | RESE 2.2Ω (JP3) — the GDEH0576T81 datasheet booster spec |

## RESE solder jumpers (JP2/JP3/JP4) — bridge exactly one

| Bridge | Rsense | Panel family |
|---|---|---|
| JP2 (default) | 0.47Ω | GDEW/GDEY (UC81xx): GDEW0154M09, GDEW0213M21, GDEW029I6FD, GDEM0154I61; proven with GDEH0576T81 too (DESPI-C02 heritage) |
| JP3 | 2.2Ω | GDEH0576T81 per its datasheet (bridge JP6 to select L2 47µH with it) |
| JP4 | 3Ω | GDEH/GDEM SSD16xx: GDEH0154Z90 (tri-color), GDEH0154D67, GDEH0213B73, GDEH029A1 |

## Bench procedures

- **PPK2 source-mode power, deployment path (used for all published board-1
  figures)**: feed J1 through a Dupont-into-JST harness, JP1 untouched. Q6
  and the MCP73831 VBAT-pin leakage are in the measurement by construction —
  true battery-terminal figures. `tools/ppk2.py` rail id: `reva-j1` (also
  what `ppk2.py sweep` sweeps for the battery-floor regime map).
- **IBAT break — battery-current (series) measurement**: cut JP1 open and
  insert a PPK2 (or any ammeter) across J2 (the 2-pin header silk-labelled
  `IBAT`, DNP by default — solder one in). Battery in JST as usual. JP1
  ships as a factory copper bridge: knife-cut it the first time, re-close
  with solder afterwards (wicking only applies to a soldered re-bridge).
- **PPK2 source-mode at J2**: feed J2 pin 2 + GND, JST empty, JP1 open.
  Pin 2 is VBAT — the charger output node, not VSYS (VSYS has no TP or
  header; probe D2's cathode pad). Powers the LDO tree + charger but
  excludes Q6. `tools/ppk2.py` rail id: `reva-j2`.
- **Do NOT back-feed the 3V3 test pad**: RT9080 abs-max forbids VOUT > VIN
  + 0.3V, and its EN=0 active-discharge (~80Ω) would fight the source.
  TP4 (3V3) is probe-only.
- Charge current: R3 10k → 100mA (0.25C for a 400–500mAh pouch). 4.99k →
  200mA if a bigger pack is fitted.
- C29 (10nF ADC reservoir on VBAT_ADC) is populated by default: enable the
  divider ~5ms before reading (τ = 50k × 10n = 0.5ms).
- BMP58x INT pins are unconnected: firmware must configure int_en=1,
  int_od=0, pad_int_drv=0 per the Bosch datasheets.
- Battery thresholds are board-scoped in Thermometer.cpp: **3550 warn /
  3500mV shutdown** (applied 2026-07-31 from the sweep + BOD-probe
  measurements, notes.md 2026-07-30 — droop at the refresh peak ≈300mV, so
  3500 keeps ~200mV of rail margin over the C6's 3.0V spec floor). That
  recovers most of the ~25% of pack capacity the buck-era 3700mV cutoff
  stranded; the cold and real-cell BOD-probe runs decide whether 3450
  (~5-8% more, OCV estimate) is safe.
- The first-article measurement list lives in [`BRINGUP.md`](BRINGUP.md)
  Phase 3 (VGH/VGL spec at refresh, EPD_VCC soft-start ramp, 3V3 sag →
  threshold re-derivation, boost ILIM transient, 32k crystal cold start,
  SS14 warm-floor leakage, VBAT_ADC sweep, charging self-heat). The 32k crystal
  is proven running warm on board 1 (no RTC fallback warning); cold start
  remains open.
- While charging, the board self-heats slightly — BMP581 temperature reads
  high until it cools; log accordingly.

## BOM

Generated at `bom/thermometer-c6-bom.csv` (JLCPCB columns) from circuit.py.
Notable parts: ESP32-C6-MINI-1-N4 (C5736265), RT9080-33GJ5 (C841192),
MCP73831-2 (C424093), Si1308EDL (C469327, low stock — fallback Si1304BDL
clone C7419947), MBR0530 TWGMC (C5204746), FPC-05FB-24PH20 dual-contact
(C2856831), SWPA4030S100MT (C38117), FC-135 (C32346), BMP581 (C5362283 —
**restocked at LCSC as of 2026-07-17** (3,675 pcs); the fab BOM populates
U5 by default. Re-verify stock at order time like everything else).

DESPI-C02 §4.5 requires an FPC socket with "contact at up side or both
side" — hence the dual-contact FPC-05FB (the bottom-contact-only
FPC-05F-24PH20 C2856805 must NOT be substituted). **Rev B anti-regression
note — this became a measured requirement on 2026-08-11, not a paper one.**
The GDEH0576T81's FPC carries its contacts on the REAR face (away from the
screen); every other panel bench-tested here — GDEM0154I61, GDEY0213M21,
GDEH0154Z90, GDEW029I6FD — has them on the FRONT. A single-side socket would
therefore have worked on every panel used during bring-up and failed on the
one panel this board is being built for. It is exactly the line item a
cost-down pass reads as unnecessary margin; it is not. J4 uses the hand-drawn
`local:XUNPU_FPC-05FB-24PH20` footprint, transcribed from the XUNPU
FPC-05FB-NPH20 manufacture drawing (pads 0.3×1.2 @0.5mm, tabs 2.0×1.8 at
±7.3/+1.625 center-to-center) and cross-checked against the EasyEDA/JLC
C2856831 land pattern — the two agree exactly. The FPC-05FB is a rear-flip
connector: the SMT contact tails / pad row sit at the REAR (actuator) face,
and the mouth / cable entry is on the far side, 4.95mm from the pad centers
(body depth 5.40 = the XUNPU drawing; VERTEX_POINT-only STEP bbox,
`out/j3-land/` §7 2026-07-20 — the earlier 6.55 came from bounding-boxing
raw CARTESIAN_POINTs, which include LINE/AXIS2_PLACEMENT_3D entities that
own no geometry). On the board J4 is placed at rot 90 with the tail/pad
column WEST (x41.45) and the mouth EAST at x46.40, so the panel cable
approaches from the east edge. The mouth sits 1.60mm inboard of the edge
rather than flush — harmless for an FPC (the cable bottoms out inside the
housing either way) and it leaves the body fully supported. Pad 1 = panel circuit 1 sits at the NORTH end (the footprint pads are
numbered to keep pin 1 north despite the rear-flip geometry; the pin-1 silk
dot marks it). Pin-1 direction is verified against the DESPI-C02 manual
photos (P1 silk: "1" and "24" end markers, "24" at the P1-refdes end); note
the DESPI "P1" silk next to the pin-24 marker is the connector refdes, not
pin 1.

## Alternate sensor: BMP585 (U6, DNP by default)

The board carries footprints for BOTH BMP581 (U5, LGA-10 2×2) and BMP585
(U6, LGA-9 3.25×3.25, media-resistant — suitable for outdoor/weather-exposed
builds; gel-protected port under the metal lid, keep the Ø2.2mm opening
unobstructed in the enclosure). Same LP I2C bus, same 0x47 strapping
(CSB+SDO→VDDIO), same register map — the firmware BMP58x driver reads the
chip-ID (0x50=581, 0x51=585) and works with either unchanged.
**Populate exactly one**: both strap to address 0x47.
BMP585 = LCSC C18184976. Its datasheet
requires a 10Ω supply series resistor only for supply ramps <10µs — not
applicable here (always-on 3V3 rail, never GPIO-gated).

## Regenerating

```
make check   # generate + ERC + netlist golden check + invariants + footprints
make pdf     # out/thermometer-c6.pdf for review
```

The `.kicad_sch` is generated by `generator/generate.py` from
`generator/circuit.py` (nets/parts) + `generator/layout.py` (placement and
drawn wire routes) — edit those, never the .kicad_sch. Connectivity is
verified three ways: generator geometric checks (cross-net coincidence =
build error), `kicad-cli` ERC at zero tolerance, and exact netlist matching
against circuit.py (anonymous `~` nets matched by pin set).

## Open items (user sign-off) — all dispositioned

1. **BMP581 sourcing** — RESOLVED 2026-07-17: restocked at LCSC (3,675
   pcs); the ordered boards populate U5 BMP581. The BMP585 (C18184976)
   remains the U6 populate-one alternate (outdoor/media-resistant builds,
   or if the 581 dries up again).
2. **Si1308EDL stock thin** — RESOLVED by the order: C469327 is on the
   boards; the fallback Si1304BDL-clone C7419947 was never needed.
3. **Reverse-polarity protection** — RESOLVED: Q6 AO3401A P-FET at the
   JST is fitted (see "Why these choices"); a reversed cell is blocked,
   MCP73831's −0.3V abs-max is respected. Proven on board 1: body diode
   0.4259V diode-mode pass ([`BRINGUP.md`](BRINGUP.md) Phase 0). Keyed JST
   + silk remain the first line of defense.
4. **EPD SPI/control series resistors omitted** — CLOSED by construction,
   no veto: boards fabbed without them, firmware floats the pins when the
   panel is gated off (src/Display.cpp), first render passed on board 1.
   Disposition recorded in [`SCHEMATIC-VERIFICATION.md`](SCHEMATIC-VERIFICATION.md).
5. **JST-PH polarity** — RESOLVED 2026-07-29 on hardware: DMM on the loose
   plug, red wire / + contact mates with J1's `+`-marked pad
   ([`BRINGUP.md`](BRINGUP.md) Phase 0). JST vs Adafruit convention still
   differs — re-check any new pigtail.
6. **FPC footprint** — DONE and hardware-verified: hand-drawn
   `local:XUNPU_FPC-05FB-24PH20` (see BOM section), respun 2026-07-19
   after a numeric STEP proof (`out/j4-proof/`), body depth corrected to
   5.40 on 2026-07-20. Placement verified pre-order (75/75 placements,
   [`archive/order-2026-07-20/`](archive/order-2026-07-20/)); J4 pin-1 north
   / mouth-east confirmed by continuity on board 1
   ([`BRINGUP.md`](BRINGUP.md) Phase 0).
7. **32k crystal populated by default** — CONFIRMED: on the ordered boards
   and proven oscillating on board 1 (no RTC fallback warning in the boot
   log); cold start remains a [`BRINGUP.md`](BRINGUP.md) Phase 3 item.
8. **Old Copilot draft** — MOOT as originally written: `hardware/kicad/`
   was never merged and exists only on the unmerged branch
   `hardware/custom-esp32c6-pcb`. Nothing in the tree to delete; the
   remaining call is whether to delete that branch.

## Follow-up phases

- PCB layout (2-layer) — **DONE**: booster switch loop tight, RESE sense
  short, no-copper zone under BMP581, antenna keep-out per Espressif HDG,
  JLCPCB gerbers/drill + CPL/BOM via `make fab` (order per
  [`ORDERING.md`](ORDERING.md)).
- Firmware — **DONE**: `THERMOMETER_C6_BOARD` variant (`thermometer_c6_*`
  envs in platformio.ini): EPD on GPIO18–23 + gate GPIO14 with float-on-off,
  battery divider GPIO2/3, VBUS sense GPIO4 (suppresses SoC shutdown on USB),
  LED GPIO15, 32k crystal via `sdkconfig.defaults.thermometer_c6`.
- Fab order — **DONE** (2026-07-20,
  [`archive/order-2026-07-20/`](archive/order-2026-07-20/); landed cost
  breakdown in [`ORDERING.md`](ORDERING.md) §8).
- Bring-up Phases 0–2 — **DONE** on board 1 (2026-07-29,
  [`BRINGUP.md`](BRINGUP.md)); measured numbers in the
  [`docs/notes.md`](../../docs/notes.md) power logbook.
- **NEXT** (hardware): [`BRINGUP.md`](BRINGUP.md) Phase 3 first-article
  measurements. Board 1 has been on battery soak since 2026-07-31 and most of
  Phase 3 waits on it. Boards 3–4 need bringing up, but not the full Phase 0–1
  checklist — board 2 skipped it and worked; only board 4's flagged U5 skew
  wants the Phase 2 sensor detect run early.

## Routed-copper census (rev A final vs the pre-connector-fix board)

`python3 verify/copper_stats.py --vs 9100758` — baseline `9100758` is the last
commit before the J4 mouth-east respin, the J3 datum/land fork and the R2.2
corners. Tracks and vias only; pours are regenerated fill, not authored copper.

```
segments   977 ->  906     -71  (-7.3%)
vias       189 ->  154     -35 (-18.5%)
F.Cu mm  756.1 -> 643.5  -112.5 (-14.9%)
B.Cu mm  840.6 -> 736.2  -104.4 (-12.4%)
total   1596.6 ->1379.7  -216.9 (-13.6%)
nets shorter 40   longer 2   ~unchanged 18   (of 60)

vias by region   FPC/east x>36  36 -> 27      USB/north y<9  51 -> 28
                 west x<20      84 -> 72
```

Putting both connectors on their true datums made the board measurably
simpler rather than merely correct: the USB/north region shed 45% of its vias
and CHG_STAT/EPD_SCK/VBUS/VBAT each lost 12–19mm. Routing style is
deliberately free-angle (≈48% of copper length off the 45/90 grid) — that is
a choice, not drift.

## Rev B candidates

The proposal register, with the research behind each row, is
[`REV-B.md`](REV-B.md). Nothing there is ordered.
