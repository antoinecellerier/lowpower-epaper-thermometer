# First complete prototype

- Firebeetle ESP32-E
- Display:
  - DESPI-C02
  - GDEW0213M21
- Sensor:
  - DS18B20-PAR
  - 4.7 kOhm resistance
- Battery:
  - RS Pro 18650 26H Li-ion Battery Pack (2.6 Ah)

| ESP32 | DESPI-C02 |
|-------|-----------|
| 3.3V  | 3.3V      |
| GND   | GND       |
| MOSI  | SDI       |
| SCK   | SCK       |
| 14/D6 | CS        |
| 2/D9  | D/C       |
| 25/D2 | RES       |
| 26/D3 | BUSY      |

| ESP32 |          | DS18B20-PAR                          |
|-------|----------|--------------------------------------|
| 4/D12 |          | DQ (middle pin)                      |
| 3.3V  | 4.7 kOhm | DQ (middle pin)                      |
| GND   |          | GND (left when looking at flat face) |

![Assembled first prototype](photos/first-prototype.jpg)

# BMP390L + ePaper setup (ULP-capable)

- Firebeetle ESP32-E
- Sensor:
  - Fermion: BMP390L Digital Barometric Pressure Sensor (Breakout, SEN0423)
- Display:
  - DESPI-C02 + GDEW0213M21 (or 1.54" Z90c tricolor)

BMP390L is wired to GPIO0/GPIO4 (RTC I2C pins) so the ULP coprocessor
can read the sensor during deep sleep.

| ESP32   | BMP390L breakout |
|---------|------------------|
| 3V3     | 3V3              |
| GND     | GND              |
| 0/D5    | SDA              |
| 4/D12   | SCL              |

# BMP58x (BMP581/BMP585) + ePaper setup (ULP-capable)

Drop-in replacement for BMP390L — same pins, same wiring. Only the I2C address
differs (0x47 vs 0x77), so both sensors can coexist on the same bus.

- Sensor:
  - Fermion: BMP581 Digital Barometric Pressure Sensor (SEN0667), or
  - Fermion: BMP585 Digital Barometric Pressure Sensor (SEN0666)

| ESP32   | BMP58x breakout |
|---------|-----------------|
| 3V3     | VCC             |
| GND     | GND             |
| 0/D5    | SDA             |
| 4/D12   | SCL             |

Set `#define USE_BMP58x` in the rig header (`include/rigs/<name>.h`). The LP
core derives `LP_CORE_BMP58X` from the same selector, so there is no second
place to change.

## DESPI-C02 power gate (FDN340P)

The DESPI-C02 adapter board draws ~534 µA quiescent due to its boost converter.
A P-channel MOSFET on the 3.3V line cuts power during deep sleep.

```
3.3V ──────┬──────── FDN340P Source (pin 2)
           │
          10kΩ
           │
13/D7 ─────┴──────── FDN340P Gate (pin 1)

DESPI-C02 3.3V ───── FDN340P Drain (pin 3)
DESPI-C02 GND ────── GND (direct)
```

GPIO LOW → display powered on. GPIO HIGH / high-Z (deep sleep) → display off.

![Firebeetle ESP32-E, BMP390L & GDEH0154Z90 (2026)](photos/firebeetle2-esp32e-bmp390l-GDEH0154Z90-prototype.jpg)

# Xiao Seed ESP32C6 + BMPxxx

- Xiao Seed ESP32C6
- Sensor:
  - Fermion BMP581
- Display + DESPI-CO2 + FDN340P
- Battery JST-2 PH-2P connectors on BAT - / +
- Current measurement - https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/#reading-battery-voltage

## Sensor

| Xiao ESP32C6      | BMP581 breakout |
|-------------------|-----------------|
| 3V3               | VCC             |
| GND               | GND             |
| LP I2C SDA (MTCK) | SDA             |
| LP I2C SCL (MTDO) | SCL             |

## Display

D9 (GPIO20) is also SPI MISO — SPI.begin() must be called with MISO=-1 before
GxEPD2 init to avoid the SPI peripheral stealing the D/C pin (e-paper is
write-only so MISO is not needed). Similarly D3 (GPIO21) is SPI SS; passing
SS=-1 prevents it claiming the BUSY pin.

| Xiao ESP32C6   | DESPI-C02 |
|-----------------|-----------|
| 3.3V            | 3.3V      |
| GND             | GND       |
| MOSI/D10 (GP18) | SDI       |
| SCK/D8 (GP19)   | SCK       |
| D6 (GP16)       | CS        |
| D9 (GP20)       | D/C       |
| D2 (GP2)        | RES       |
| D3 (GP21)       | BUSY      |

D7 (GP17) for the MOSFET Gate

## Battery voltage divider (GPIO-switched)

Seeed documents a 200kΩ/200kΩ (or 220kΩ) always-on divider, but that draws
~10µA continuously — almost doubles the deep sleep floor. A GPIO-switched
divider with an N-channel MOSFET eliminates quiescent draw entirely.

**Components:** 2× 100kΩ resistors + AO3400A (N-channel MOSFET, SOT-23)

```
Bat+ ─── 100kΩ ─── A0 (D0) ─── 100kΩ ─── AO3400A Drain
                                                │
                                             Source ─── GND
                                                │
                                        Gate ←── D1 (GP1)
```

- D1 HIGH → MOSFET on, divider active, A0 reads Vbat/2
- D1 LOW / deep sleep → MOSFET off, zero divider current
- R_source = 50kΩ → ADC settles in ~2µs, minimal averaging needed
- When MOSFET off, A0 floats toward Vbat through 100kΩ; leakage through
  the ADC's ESD clamp is ~(4.2−3.9V)/100kΩ ≈ 3µA — but only through the
  internal protection diode, negligible in practice

**Read sequence:** set D1 HIGH, delayMicroseconds(100), analogRead(A0) a
few times for noise averaging, set D1 LOW. Total on-time <1ms.

**Why 100kΩ, not 1MΩ:** with 1MΩ/1MΩ (R_source = 500kΩ), the ESP32 SAR
ADC sample window (~300ns) is far too short for the RC to settle — readings
are biased low, not just noisy, and averaging doesn't fix bias. 100kΩ/100kΩ
settles in ~2µs which is still longer than the sample window but close enough
that a few back-to-back reads converge. Adding a 100nF buffer cap at A0 would
allow higher resistance values (charges in 5×R_source×100nF) but adds a
component for no real benefit when the divider is switched off during sleep.

## Unused pins

Breakout:
VBUS
D4
D5

Under board:
MTDI
GND
EN
MTMS
3V3
BOOT

![Seeed Xiao C6, BMP581 & GDEH0576T81 (2026)](photos/seeed-xiao-c6-bmp581-GDEH0576T81-prototype.jpg)

# Seeed ePaper Driver Board for XIAO vs DESPI-C02 (compatibility notes)

Researched 2026-07-04 from the Seeed
[wiki](https://wiki.seeedstudio.com/xiao_eink_expansion_board_v2/), its schematic
(`hardware/Seeed ePaper Driver Board for XIAO SCH v1.0.pdf`) and the DESPI-C02
spec (`hardware/DESPI-C02 Connector Board for E-paper Display V1.1.pdf`). The
Seeed board copies Good Display's reference booster; Seeed's own panels are
rebranded GD units.

| | DESPI-C02 | Seeed ePaper Driver Board |
|---|---|---|
| Panel connector | 24-pin 0.5mm FPC, standard Good Display pinout | identical |
| Logic and supply | 3.3V | identical |
| Boost circuit | 10µH inductor, Si1304BDL MOSFET, MBR0530-class Schottkys, 4.7µF/50V cap | identical parts; B0540WS Schottkys |
| RESE | 0.47Ω / 3Ω select switch | fixed 0.47Ω (R2, no alternate footprint) |
| Power gate | needed: ~534µA ungated | none, and none needed: ungated standby adds ~9.3µA over the DESPI-gated baseline |
| Battery path | none | ETA9740 charger (0.5A) + JST-PH + power switch; do not use, see below |
| Pin mapping | free-form | fixed, table below |

Good Display warns a wrong RESE "will cause the e-paper cannot be refreshed"; in
practice a 3Ω panel on 0.47Ω often still refreshes, out of spec, with a stressed
booster and a degraded image. Per the DESPI-C02 spec, 0.47Ω suits GDEW/GDEY
(UC81xx), most newer panels and four-color panels, e.g. GDEW042T2, GDEW075T7; 3Ω
suits mostly older GDEH/GDEM SSD16xx panels (GDEH0154D67, GDEH0213B73,
GDEH029A1) plus the oddballs GDEW0583T7 and GDEW075T8. Naming is not a reliable
guide (two GDEW panels need 3Ω): read the RESE value off the panel datasheet's
reference circuit before plugging in.

| Panel | Wants | On the Seeed board |
|---|---|---|
| GDEW029I6FD | 0.47Ω | fine, verified working 2026-07-05, first flash |
| GDEH0154Z90 | 3Ω (GDEH/SSD1681) | mismatched |
| GDEH0576T81 | 2.2Ω + 47µH inductor | out of spec (board is 0.47Ω + 10µH), untested |

Fixed pin mapping (firmware must match):

| Signal | XIAO pin |
|--------|----------|
| RST    | D0       |
| CS     | D1       |
| BUSY   | D2       |
| DC     | D3       |
| SCK    | D8       |
| MOSI   | D10      |

Three rules:

- **Do not use the JST battery connector.** The ETA9740 path idles at ~330-500µA,
  ~20× the rest of the system, and the switch does not isolate it: its OUT pin is
  hardwired to the XIAO 5V pin, so the IC powers up whenever USB is plugged in.
  Solder the cell to the XIAO's underside BAT pads, JST empty, switch off
  ([notes.md, battery path via the shield JST](notes.md#seeed-xiao-epaper-driver-board-battery-path-via-the-shield-jst-2026-07-05)).
- **No power gate.** 3V3 is hardwired to the booster and FPC; the ungated
  standby measures ~25.1µA, +9.3µA over the DESPI-gated baseline, against the
  DESPI-C02's ~534µA ungated
  ([notes.md, rail-fed floor](notes.md#seeed-xiao-epaper-driver-board-rail-fed-floor-and-refresh-2026-07-05)).
- **A battery divider is still possible, not built.** The mapping takes D0/D1
  and leaves nothing ADC-capable on the header, but the underside pads MTMS
  (GPIO4, ADC1_CH4) and MTDI (GPIO5, ADC1_CH5) are free, LP I2C being on MTCK/MTDO
  (GPIO6/7). Sense on MTDI, AO3400A gate on D4 or D5, the 100k/100k divider above.
  XIAO thresholds in `Thermometer.cpp` are 3800/3700 mV from the 2026-07-05 fine
  sweep: 3.7V is the lowest verified-healthy point, 3.6V is inside the sag band.

The 2026-07-04 verification list is closed. Every measurement on this board is in
`notes.md`, 2026-07-05, source voltage recorded per figure:
[ungated standby](notes.md#seeed-xiao-epaper-driver-board-rail-fed-floor-and-refresh-2026-07-05),
[JST path](notes.md#seeed-xiao-epaper-driver-board-battery-path-via-the-shield-jst-2026-07-05),
[BAT-pads sweep](notes.md#xiao-c6-battery-direct-on-the-bat-pads-voltage-sweep-2026-07-05),
[buck regime map](notes.md#xiao-c6-buck-sag-mechanism-and-shutdown-thresholds-2026-07-05). Compare in mJ, not mC: the three configs meter
at different node voltages. The buck's usable window ends around 3.6-3.7V, a
firmware threshold rather than a wiring choice; below it wakes collapse into
brownout storms.

Still open, on the custom board rather than this one: a cold (~0°C) run and a
refresh on a real cell, which together decide the final shutdown threshold
([BRINGUP.md](../hardware/thermometer-c6/BRINGUP.md) Phase 3).

![Seeed Xiao C6, e-Paper Driver Board, BMP581 & GDEW029I6FD (2026)](photos/seeed-xiao-c6-bmp581-epaperhat-GDEW029I6FD-prototype.jpg)

# Custom board (thermometer-c6 rev A)

Not covered here — this file is the dev-board prototype wiring. The rev A pin
map, jumper tables and bench procedures live in
[`hardware/thermometer-c6/README.md`](../hardware/thermometer-c6/README.md).

![Thermometer C6 rev A board 1 & GDEM0154I61 (2026)](photos/revA-GDEM0154I61.jpg)

![Thermometer C6 rev A boards 2 and 4 & GDEH0576T81 (2026)](photos/revA-GDEH0576T81.jpg)

