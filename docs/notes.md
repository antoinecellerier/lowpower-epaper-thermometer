# First long run

|stats         | value               |
|--------------|---------------------|
| first boot   | 2021-10-29 17:14:54 |
| last refresh | 2021-11-08 05:39:40 |
|              |includes +1 hour due to DST|
| seq          | 131014              |
| refresh      | 859                 |
| bat          | 2998 mv             |

bat 2954 mV at 2021-11-08 11:30 ... something's draining current even when shut down

ran for 739486 seconds = 8.5 days

3.2 => 3 V took a few hours only (didn't see the 3.2 V warning display)
battery rated for 2.6Ah (9.62Wh)

=> ~12.6 mA average consumption which is x1000 more than deep sleep target (~10µA)

Assumptions without proper multi-meter measurments
* deep sleep is not measurable probably < 1 mA lets assume ~0.5mA
* each wake up takes 2s at 40mA
* each refresh takes 15s at 50mA
* each screen clear takes 30s at 50mA

* 2s wake-up is 91% of energy budget, deep sleep is 3% of energy budget
* 1s wake-up is 83% of energy budget, deep sleep is 6% of energy budget
* 0.5s wake-up is 72% of energy budget, deep sleep is 10% of energy budget

1.5s wake-up => ~2.5 Ah

First priority: save on wake-up time/energy consumption
- 40 mA is inline with measurements at https://diyi0t.com/reduce-the-esp32-power-consumption/
- Adjust CPU frequency to 80 MHz? (defaults to 240 MHz)
- Use ULP to probe temperature? https://www.youtube.com/watch?v=-QIcUTBB7Ww https://github.com/fhng/ESP32-ULP-1-Wire https://github.com/duff2013/ulptool https://github.com/espressif/arduino-esp32/issues/1491 https://github.com/platformio/platform-espressif32/issues/95 

Other TODOs:
- Use ESP-IDF logging facilities https://thingpulse.com/esp32-logging/
- Use PROGMEM https://www.e-tinkers.com/2020/05/do-you-know-arduino-progmem-demystified/


# Current measurement first soldered prototype Nov 30 2021

https://wiki.dfrobot.com/FireBeetle_Board_ESP32_E_SKU_DFR0654 see "Low Power Pad"

Measurements with UT61E+

Powered at 4V on VCC

Typical powered consumption: ~ 45 mA

With Low Power Pad not cut: ~ 490 µA

With Low Power Pad cut: ~ 71 µA / Sometimes ~125 µA ?!? / and the following day ~39 µA ?!?!?

With setup calling pinMode(2, OUTPUT or 0) and going directly to sleep and all components connected ~ 66 µA

With setup directly going to deep sleep and all components connected ~ 27 µA in deep sleep

With setup directly going to deep sleep and all components connected except DS18B20-PAR's data ping ~ 25 µA deep sleep

Board with no connections other than VCC & GND consumes ~ 14 µA in deep sleep

# Current measurement impact of light sleep during DS18B20 temp measurment

Measurements with UT61E+. The sampling and value refresh rates are a bit slow (a few 100 ms each). Values are in mA.

Wifi was disabled.

DS18B20 temperature measurement last ~750ms

DS18B20 with normal delay during measurement:
![DS18B20 normal delay during measurement](thermometer-normal.jpg)

DS18B20 with light sleep during measurement:
![DS18B20 light sleep during measurement](thermometer-with-light-sleep.jpg)

BMP390L during measurement (no display):
![BMP390L temperature measurement](thermometer-bmp390l.jpg)

# ULP coprocessor power measurements (March 2026)

Setup: FireBeetle ESP32-E with BMP390L sensor and ePaper display connected.
Measured with Nordic PPK2 on VCC. Low Power Pad cut.
Board: dfrobot_firebeetle2_esp32e, PlatformIO + Arduino framework.

## Test conditions

All measurements are 1-minute averages in steady state (excluding initial boot spike).

| Config | Sleep interval | ULP period | CPU wakes? | Avg current | Notes |
|--------|---------------|------------|------------|-------------|-------|
| Bare sleep (no init, straight to sleep) | N/A | N/A | Never | ~510 µA | No serial, sensor, or display init |
| No ULP (indefinite deep sleep) | N/A | N/A | Never | ~560 µA | Normal boot, sensor+display init, then sleep |
| ULP test (counter, no wake) | 5s ULP timer | 5s | Never | ~560 µA | ULP runs every 5s, increments counter, halts |
| ULP test (counter, no I2C) | 5s ULP timer | 5s | Every 15s (3 cycles) | — | Functional test only, not measured in steady state |
| **ULP bit-bang I2C (production)** | **5s** | **5s** | **On ≥0.1°C change** | **~562 µA** | **HULP bit-bang I2C, delta threshold=20** |

**Key findings:**
- ULP bit-bang I2C with full BMP390L temp reading: ~562 µA average deep sleep
- ULP overhead is negligible (~0 µA difference with/without ULP running)
- **With EPD VCC disconnected: ~28 µA** — essentially bare-board baseline
- **The DESPI-C02 ePaper adapter board draws ~534 µA quiescent** — this is the dominant power consumer
- ULP + RTC_PERIPH + BMP390L adds only ~1 µA above the 27 µA bare-board baseline
- Hardware RTC I2C peripheral could not be made to work (BUS_BUSY stuck, see docs/rtc-i2c-research.md)
- GPIO pin isolation (hold RST LOW, float SPI) does not reduce the DESPI-C02 draw — it's a hardware issue

## DESPI-C02 quiescent current (known hardware issue)

The ~534 µA overhead is a known issue with the DESPI-C02 adapter board. The board's boost converter
capacitors leak current even after the display controller is put into deep sleep (command 0x07).

- **Confirmed by other users**: https://github.com/ZinggJM/GxEPD2/discussions/142
  (same symptoms: ~500 µA in deep sleep, drops to ~50 µA when removing DESPI-C02 3.3V)
- **DESPI-C02 manual §4.6**: "The high current in deep sleep mode may be due to the larger
  capacitance in the boost part."
- **PPK2 trace** shows ~10ms oscillating spikes to 4-5 mA — characteristic of a boost converter
  periodically charging even in standby.
- **Software mitigations tested and ineffective**: holding RST LOW via gpio_hold_en,
  floating SPI/CS/DC pins, calling SPI.end() — none reduced the current.

### Possible fixes (all hardware)
1. **Power-gate the DESPI-C02** with a P-channel MOSFET (e.g., Si2301, AO3401) on its 3.3V line,
   controlled by a GPIO + 10kΩ pull-up. GPIO HIGH = off (sleep), GPIO LOW = on (refresh).
   FireBeetle ESP32-E has no built-in controllable 3.3V output, so this requires an external MOSFET.
2. **Replace the DESPI-C02** with direct panel wiring using the panel's spec capacitors
3. **Use a different adapter board** with better sleep characteristics

### Fix implemented: FDN340P power gate (March 2026)

P-channel MOSFET (FDN340P, SOT-23) on the DESPI-C02 3.3V line, gate driven by GPIO13/D7
with 10kΩ pull-up to 3.3V. See [`docs/wiring.md`](wiring.md) for circuit details.

- **Deep sleep with power gate: ~18 µA average** (down from ~562 µA)
- MOSFET cuts all power to DESPI-C02 during deep sleep (GPIO goes high-Z, pull-up holds gate at VCC)
- Software: `EPD_POWER_GATE` define in `local-secrets.h` enables power control in `Display.cpp`
- `epd_power_on()` drives GPIO13 LOW + 10ms delay before display init
- `epd_power_off()` drives GPIO13 HIGH after display hibernate

![BMP390L + ULP + P-FET temperature measurement](thermometer-deepsleep-pfet.png)

### Adafruit 1.54" eInk breakout — tested and rejected

The Adafruit 1.54" Tri-Color eInk breakout (ThinkInk, product #3625) was tested as an alternative.
Despite having an onboard LDO with an Enable pin, it performed **much worse**:

- **With EN floating (default):** ~3 mA average, 21 mA spikes — display controller in active state
- **With EN tied directly to GND:** ~5.5 mA average, 20 mA spikes — still drawing heavily
- Current likely back-feeds through SPI pin ESD diodes and/or microSD + SRAM components
- The board's additional components (SPI SRAM, microSD socket) create parasitic current paths
  that bypass the LDO even when disabled
- **Conclusion:** Adafruit board is ~10x worse than DESPI-C02 for deep sleep. Not suitable.

## Reference values (from earlier measurements)

- Bare board deep sleep (no connections): ~14 µA
- All components connected, setup goes straight to sleep: ~27 µA
- Previous long-run average (wake every 60s, display refresh): ~12.6 mA

## ULP bit-bang I2C implementation notes

- Uses HULP library (`hulp_i2cbb.h`) for ULP GPIO bit-bang at ~150 kHz
- BMP390L protocol: write PWR_CTRL for forced mode → 7ms delay → read 3 temp bytes
- Delta comparison on DATA_1 (middle byte), threshold=20 (~0.1°C per count)
- Compensation done on main CPU after wake using calibration data cached in RTC memory
- `hulp_peripherals_on()` sets `ESP_PD_DOMAIN_RTC_PERIPH = ESP_PD_OPTION_ON` — adds negligible current (~1 µA)

## Debug GPIO pins

- D10/GPIO17 → PPK2 D0: HIGH while main CPU is active
- D11/GPIO16 → PPK2 D1: HIGH during display refresh
- D13/GPIO12 → PPK2 D2: HIGH while ULP executing (requires `PPK2_DEBUG_ULP_GPIO` flag + RTC periph power)

Note: `PPK2_DEBUG_ULP_GPIO` forces RTC peripherals on during deep sleep, which increases sleep current. Keep disabled for accurate measurements.

## Observations

- ULP GPIO debug (D13) initially didn't show signal — fixed by removing `rtc_gpio_hold_en()` which was blocking ULP register writes
- The 562 µA with ULP bit-bang I2C is ~20x better than old wake-every-cycle (~12.6 mA) but ~20x above bare deep sleep floor (~27 µA)
- The dominant cost was the DESPI-C02 ePaper adapter board (~534 µA quiescent, known hardware issue — see section above)
- With EPD disconnected, total sleep current is ~28 µA (ULP + BMP390L + RTC_PERIPH ≈ 1 µA overhead)
- **Resolved:** FDN340P power gate on DESPI-C02 VCC brings deep sleep to ~18 µA — below bare-board baseline (pull-up likely reduces leakage paths)

# XIAO ESP32C6 power measurements (March 2026)

Setup: Seeed XIAO ESP32C6, bare board (no peripherals connected).
Measured with Nordic PPK2 on 3.3V pin (bypassing onboard LDO). Source voltage 3320 mV.
Board: seeed_xiao_esp32c6, PlatformIO + pioarduino (Arduino Core 3.x / ESP-IDF 5.x).

## Critical finding: ARDUINO_USB_CDC_ON_BOOT

The XIAO ESP32C6 board definition sets `ARDUINO_USB_CDC_ON_BOOT=1` by default, which keeps
the ESP32-C6's built-in USB Serial/JTAG controller active during deep sleep. This draws ~20 mA
constantly, completely masking deep sleep savings.

**Fix:** Add to platformio.ini env:
```ini
build_unflags = -DARDUINO_USB_CDC_ON_BOOT=1
build_flags = ... -DARDUINO_USB_CDC_ON_BOOT=0
```

Note: `-UARDUINO_USB_CDC_ON_BOOT` in build_flags alone doesn't work — PlatformIO's board
`extra_flags` are applied separately. Must use `build_unflags` to remove the board flag.

## Test results

| Config | Sleep interval | Avg current (steady state) | Deep sleep floor | Notes |
|--------|---------------|---------------------------|-----------------|-------|
| USB CDC ON (default board config) | 5s | ~20.65 mA | ~20 mA | USB Serial/JTAG stays active — unusable |
| USB CDC OFF, no WiFi, no LEDs, no display | 5s | ~415 µA | ~14 µA | Bare minimum config, DummySensor |
| USB CDC OFF, WiFi on first boot, no display | 5s | ~428 µA | ~16 µA | WiFi.disconnect(true,true) fully powers down radio |

## LP Core ULP (LP_CORE_IDLE mode, March 2026)

Setup: Bare XIAO ESP32C6, no BMP390L connected. USB CDC OFF. LP core running in idle mode
(no I2C, simulates sensor timing with 7ms delay). LP timer wakeup source. PPK2 at 3320 mV.

| Config | LP timer interval | WAKE_EVERY | HP wakes every | Deep sleep floor | Notes |
|--------|------------------|------------|----------------|-----------------|-------|
| LP_CORE_IDLE | 5s | 6 | 30s | ~15 µA | LP spikes ~1mA, HP spikes 20-50mA |

**Key findings:**
- 15 µA deep sleep baseline — LP core timer + shared memory adds negligible overhead
- LP core wakeup spikes: ~1 mA (7ms simulated sensor read time)
- HP (main CPU) wakeup spikes: 20-50 mA (DummySensor, no WiFi, no display)
- 1-minute average: ~90 µA (dominated by HP wakeups every 30s)
- In production with BMP390L I2C mode + 60s LP timer, HP wakes only on ≥0.1°C temp change

### Pending: BMP390L mode testing (never done — the C6 shipped on BMP58x)
- Awaiting soldering station to connect BMP390L to C6 board
- Switch `ulp/lp_core_main.c` from `#define LP_CORE_IDLE` to BMP390L I2C mode
- Verify LP I2C reads work (GPIO6=SDA, GPIO7=SCL, LP_I2C_NUM_0)
- Measure LP core power with real I2C transactions vs idle delay
- Tune TEMP_DELTA_THRESHOLD (currently 20 ≈ 0.1°C) and SLEEP_INTERVAL_S (60s for production)

## Pending: BMP58x mode testing (April 2026)

> **Superseded — hardware validation happened 2026-04-21** (the measured section
> at the end of this block), then again post-migration in the July sections
> below. The unticked boxes here were either answered there or absorbed into the
> 2026-07-26 budget; the ESP32-E comparison figures predate the FDN340P gate.
> Kept as the record of what was asked before the board was wired.

Current C6 production setup uses BMP58x (BMP581/BMP585) via LP core, not BMP390L.
Code complete; hardware validation queued.

**Context — forced-mode fix applied 2026-04-19:** `ODR_CONFIG` previously wrote `0x01`
which is `BMP5_POWERMODE_NORMAL` per Bosch's `bmp5_defs.h`, not forced. Sensor was
sampling continuously at default ODR 240 Hz between wakes (~200 µA continuous).
Now writes `0x02` (`BMP5_POWERMODE_FORCED`) — sensor runs one measurement then
auto-returns to standby. All deep-standby entry conditions now hold (deep_dis=0,
FIFO off, IIR off, ODR=0), so the sensor auto-enters deep standby (~0.5 µA)
between wakes without any extra code.

Hardware preparation:
- Solder BMP581 or BMP585 to XIAO C6 (SDA=GPIO6, SCL=GPIO7, I2C addr `0x47`)
- Switch `ulp/lp_core_main.c` from `#define LP_CORE_IDLE` to `#define LP_CORE_BMP58X`
- Set `SLEEP_INTERVAL_S=60` and `WAKE_EVERY=1` (60s LP timer, HP wake on delta only)
- Confirm `USE_BMP58x` in `local-secrets.h`

### Measurements needed to confirm full C6 operation

Baseline / correctness:
- [x] **Deep sleep floor with BMP58x connected, steady temperature.** Measured ~14 µA on 2026-04-21 (SLEEP_INTERVAL_S=5, no HP wakes in window) — matches the 15–16 µA expectation, well below the 200 µA forced-mode-broken threshold.
- [ ] **Confirm sensor is in deep standby between wakes.** Between LP core spikes, sensor contribution should be ~0.5 µA (not ~1 µA standby). If the measurement can't resolve that, alternative check: read `ODR_CONFIG` back via HP I2C right after deep-sleep exit — `pwr_mode` bits [1:0] should read `00` (standby). (Indirectly supported by the 14 µA floor, but not directly verified.)

LP core wake characterisation:
- [x] **LP core spike duration.** Measured ~3 ms on 2026-04-21 — matches the predicted 3.5–4 ms window and confirms the OSR-write removal shortened the spike vs the 7 ms LP_CORE_IDLE baseline.
- [x] **LP core spike amplitude.** Measured ~1 mA peak; stepped shape from sensor conversion not separately resolved at this zoom.
- [ ] **Charge per LP wake** (integrate current × time). Use PPK2 area measurement. Multiply by wakes/hour (3600/60 = 60) to project hourly load. (Rough estimate from spike shape: ~3 µC/wake → ~180 µC/hour ≈ 50 nA avg at 60s interval.)

HP wake characterisation:
- [ ] **HP wake duration with BMP58x** — expected shorter than DummySensor (no sensor bring-up overhead since sensor is already in deep standby). No display refresh if temp delta small.
- [ ] **Delta-wake trigger.** Heat sensor with finger; confirm HP wake fires when LP-core delta ≥25 counts (~0.1 °C). Measure HP spike shape during a real delta-triggered wake.
- [ ] **Safety-net HP wake** — confirm the periodic safety wake fires at the configured cadence (for hourly/daily bucket finalisation).

Averages:
- [ ] **1-minute average at steady state** (no delta wakes): should be ~15 µA baseline + (LP wake charge) × 1/min. Target **<30 µA**.
- [ ] **1-hour average at steady state** — dominated by 60 × LP wakes + occasional safety-net HP wake.
- [ ] **1-hour average under slow drift** (e.g., room temp drifting 1 °C/hour → ~10 delta wakes/hour) — characterises typical indoor use.

Regression checks vs prior measurements:
- [x] Compare C6 BMP58x deep sleep floor against C6 LP_CORE_IDLE floor (~15 µA). Measured 14 µA on 2026-04-21 — within 1 µA, no regression.
- [ ] Compare against ESP32-E BMP390L production (~562 µA with DESPI-C02 attached, ~28 µA without). C6 has no DESPI-C02, so C6 floor should track bare-board baseline.

PPK2 GPIO markers (reuse existing scheme from ESP32-E): tag LP-core-active and HP-active pins so the trace can be segmented automatically.

### Measured 2026-04-21 (BMP581 on XIAO C6, LP_CORE_BMP58X, SLEEP_INTERVAL_S=5)

Setup: XIAO ESP32-C6 + BMP581 (I2C on GPIO6/7, addr 0x47) + GDEH0576T81 e-paper, `seeed_xiao_esp32c6_release` env (USB CDC off, DISABLE_SERIAL). PPK2 at 3.32 V.

- Deep sleep floor: **~14 µA** (steady room temp, no HP wakes in window).
- LP core wake spike: **~3 ms at ~1 mA** (see `docs/xiao-seeed-esp32c6-bmp581-deep-sleep-i2c-lp-core-read.png`) — matches the expected 3.5–4 ms window (shorter than the 7 ms LP_CORE_IDLE baseline, as predicted after dropping the per-wake OSR write).
- Screen refresh (GDEH0576T81 full update): **~3.2 s at ~29 mA avg, ~322 mA peak, ~93 mC charge** per refresh (see `docs/xiao-seeed-esp32c6-bmp581-GDEH0576T81-screen-refresh.png`). Dominates the energy budget whenever it fires — at one refresh/hour this alone averages to ~26 µA.
- Gotcha: after a warm reset (reflash or HP restart), PPK2 briefly showed extra ~200 ms spikes on top of the LP-core cadence. They **did not reappear after a full cold boot** (power cycle). Suspected leftover PMU/LP-clock state from the previous run; not investigated further since it's self-clearing.


# Post-espidf-migration power measurements (July 2026, IDF 6.0.1, PPK2)

All figures are config-specific: panel, sensor and board all matter. Supply
node is not recorded for the July entries; the readme lists them as
`@3V3 rail` (see Open items).

## XIAO ESP32-C6 + BMP581 + GDEH0576T81 (920x680), release build (July 2026)

Parity with the Arduino-era firmware: deep sleep 15.5-16 µA, refresh 3.2 s
and ~95 mC.

| Quantity | Value | Arduino era | Note |
|---|---|---|---|
| Deep sleep | 15.5-16 µA | ~15 µA | USB-Serial-JTAG console (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG`) harmless asleep |
| Temp-refresh wake | 3.2 s, ~95 mC | 3.2 s, ~93-95 mC | render + SPI push + full refresh |
| Trace shape | ~1.5 s flat ~35 mA, then waveform bursts, ~465 mA peak | | |

At one refresh/hour the refresh alone averages ~26 µA and dominates the budget.
The Arduino-era `ARDUINO_USB_CDC_ON_BOOT` ~20 mA trap no longer exists.

## FireBeetle 2 ESP32-E + BMP390L + GDEH0154Z90 (200x200 3-color), release build (July 2026)

Deep sleep 19-20 µA with the FDN340P gate and ULP FSM polling; Arduino era
~18 µA on the same rig, parity within measurement variance.

The Z90 full refresh exceeds GxEPD2's hardcoded 20 s busy timeout, so a benign
"Busy Timeout!" prints every refresh (pre-existing, ungated by the diag flag).
Each refresh keeps the CPU awake the full ~21 s on this panel.

## Light sleep during the EPD busy-wait (July 2026)

Refresh charge fell 41% on the C6/T81 and 77% on the E/Z90.

Mechanism: GxEPD2 `setBusyCallback` → `esp_light_sleep_start()` with a
level-agnostic GPIO wake on BUSY and a timer backstop; wake sources disarmed
after each slice. It needs `gpio_sleep_sel_dis` on CS/DC/RST/SCK/MOSI and on
the EPD power-gate pin (otherwise pins switch to their sleep config each slice
and a started refresh ends in faint noise), and the C6's TOP power domain held
ON during slices for the GPSPI register state, restored to AUTO after.

| Rig | Before | After | Evidence |
|---|---|---|---|
| C6/T81, release | 95.4 mC, 3.2 s | **56.25 mC**, ~3.8 s (backstop granularity) | `xiao-seeed-esp32c6-bmp581-GDEH0576T81-screen-refresh.png` → `xiao-seeed-esp32c6-bmp581-GDEH0576T81-screen-refresh-light-sleep.png` |
| E/Z90, release, 100 ms backstop | 600 mC (~24 mA spin-wait band over ~21 s) | 139 mC (~6.4 mA avg: ≈40 mC active + ≈100 mC panel drive and floor) | `firebeetle2-esp32e-bmp390l-GDEH0154Z90-screen-refresh.png` → `-light-sleep.png` |
| E/Z90, backstop 100 → 500 ms | 139 mC | ~129 mC | free on latency: the GPIO wake ends each wait |

The estimate was ~27%; light sleep also covers the power-on/off busy waits.
Deep sleep is unaffected (~15.5 µA). At one refresh/hour: C6 refresh share
~26.5 → ~15.6 µA, total ~42 → ~31 µA (~40% below the Arduino-era firmware);
E refresh share ~167 → ~39 µA, total ~186 → ~58 µA, about 3× battery life at
that cadence. Savings scale with busy duration, so slow panels gain most.

## ULP wake latch: refresh trains (July 2026)

Fixed: one refresh per wake, wakes spaced at the 60 s poll cadence from the end
of the previous refresh, no cold-boot phantom refresh (E/Z90 release, PPK2).

Symptom: bursts of ~3 back-to-back refreshes with ~2 s gaps, then a clean 60 s
sleep. Cause: the ULP FSM programs called `I_WAKE` unconditionally; a wake
signalled while the host was awake (the Z90 renders ~21 s, overlapping a 60 s
poll) latches in RTC_CNTL and fires on deep-sleep entry. Pre-existing, visible
in Arduino-era debug logs, not caused by the light-sleep change. Fix: gate
`I_WAKE` on `RTC_CNTL_RDY_FOR_WAKEUP` and skip without updating the delta
reference. Siblings from the same fix: delta reference seeded on first run
(cold boots double-refreshed), ULP size checked at build time
(`scripts/check_ulp_size.py`, validated 127/128 against the on-device count
and proven to fail the old 129-word regression) with a runtime fallback of
log plus safety-net wakes instead of an abort loop.

Open:
- C6 LP-core BMP58x branch (`ulp/lp_core_main.c`) calls
  `ulp_lp_core_wakeup_main_processor()` unconditionally too. The 5.76" rig is
  awake ~3.8 s per cycle (~6% collision chance at 60 s polls). Gating needs a
  PMU HP-sleep-state check from LP-core code; do it if trains appear.

## Skip app image validation on deep-sleep wake (July 2026)

E/Z90 active phase 40 → 22.5 mC; the skipped SHA256 pass was ~1 s of wall
time against a ~250-400 ms estimate.

`CONFIG_BOOTLOADER_SKIP_VALIDATE_IN_DEEP_SLEEP=y` (sdkconfig.defaults, both
boards). The 2nd-stage bootloader re-hashed the ~1MB app over DIO/40MHz flash
on 100% of wakes, including no-refresh safety-net wakes. Power-on and reset
boots still validate. Uses the 16-byte bootloader RTC-FAST retain area; ULP
and `RTC_DATA_ATTR` live in RTC slow memory, overlap check OK.

| Quantity, E/Z90 release, n=2 wakes | Before | After |
|---|---|---|
| Active phase (boot + ULP read + render + push) | ~40 mC, ~1.7 s | **22.5 mC**, 710 ms at ~32 mA |
| Full refresh event | ~129 mC | 114.5 mC, 19.0 s at 6.01 mA |
| Deep-sleep floor, retain area powered | 19-20 µA | ~19.4 µA |

Evidence: `firebeetle2-esp32e-bmp390l-GDEH0154Z90-wake-active-phase-skip-validate.png`,
`firebeetle2-esp32e-bmp390l-GDEH0154Z90-screen-refresh-skip-validate.png`.
C6 figures: the combined entry below.

## Flash QIO/80MHz, tried and reverted (July 2026)

Worse: active phase 22.5 → 25.2 mC. Reverted to DIO/40MHz.

| Quantity, E/Z90 | DIO/40MHz | QIO/80MHz |
|---|---|---|
| Active phase | 710.5 ms, 31.7 mA, 22.5 mC | 697.3 ms (−13 ms), 36.1 mA (+4.4 mA), **25.2 mC** |
| Full refresh event | 114.5 mC | ~116 mC |

With validation skipped the active phase is CPU-bound, not flash-read-bound,
and faster flash clocking costs current across the whole window. Before
skip-validate, with the ~1 s SHA256 pass present, QIO would likely have won.

## Compile at -Os (July 2026)

E/Z90 active phase 22.5 → 20.6 mC, full refresh 114.5 → 112 mC, binary
1014 → 938 KB.

IDF builds default to -Og regardless of PlatformIO's `build_type=release`
(verified in compile_commands.json: all 908 app TUs). Now
`CONFIG_COMPILER_OPTIMIZATION_SIZE=y` in sdkconfig.defaults for both boards,
debug envs included (they exist for serial logs, not JTAG stepping).

| Quantity, E/Z90 release | -Og | -Os |
|---|---|---|
| Active phase | 22.5 mC, 710 ms | **20.6 mC**, 640 ms at ~32 mA |
| Full refresh event | 114.5 mC | 112 mC |
| Binary | 1014 KB | 938 KB |

Zoomed active phase (1 s window): ~90 ms ROM + bootloader, a one-sample ~405 mA
spike at EPD power-gate turn-on (boost inrush), a flat ~33 mA band to ~620 ms
(IDF bring-up + render + SPI push ≈ 12.5 mC), then panel drive. Evidence:
`firebeetle2-esp32e-bmp390l-GDEH0154Z90-wake-active-phase-Os.png`,
`firebeetle2-esp32e-bmp390l-GDEH0154Z90-screen-refresh-Os.png`.

Running total, E/Z90 per refresh event:

| Stage | Refresh event | Active phase |
|---|---|---|
| spin-wait era | 600 mC | 40 mC |
| busy-wait light sleep | 129 mC | |
| skip validation | 114.5 mC | 22.5 mC |
| -Os | **112 mC** | 20.6 mC |

## C6: skip-validate and -Os combined (July 2026)

Full refresh 56.25 → 45.3 mC (−19%) on the XIAO C6 + BMP581 + GDEH0576T81
release build; the two effects were separated only on the E above.

| Quantity | Before | After |
|---|---|---|
| Active phase (boot + render + SPI push) | 28.5 mC, 1.08 s at 26.4 mA | 18.3 mC, 0.80 s at 22.9 mA |
| Full refresh event | 56.25 mC | **45.3 mC** |
| Refresh share at 1/hour | ~15.6 µA | ~12.6 µA |
| Binary | 1080 KB | 983 KB |
| Deep-sleep floors, retain area powered | 15.5-16 µA C6, 19-20 µA E | ~15.8 µA C6, ~19.4 µA E |

Evidence: `xiao-seeed-esp32c6-bmp581-GDEH0576T81-wake-active-phase-pre-skip-validate.png`
(before), `-wake-active-phase-skip-validate-Os.png` and
`-screen-refresh-skip-validate-Os.png` (after). A wrong screen/sensor config in
this session panic-looped at ~600 ms and read as a ~670 µA floor with 25 mA
pings; the stale e-paper frame is the tell (`/device-session`).

## Seeed XIAO ePaper Driver Board, rail-fed floor and refresh (2026-07-05)

Ungated shield standby costs ~9.3 µA over the DESPI-gated baseline; not worth a
power-gate mod.

Conditions: XIAO C6 + BMP581 + Seeed ePaper Driver Board (fixed RESE 0.47 Ω,
no power gate) + GDEW029I6FD (2.9" 296x128), `seeed_xiao_esp32c6_epaper_release`,
PPK2 source meter 3.3 V into the 3V3 rail. The ETA9740 battery path is
unpowered in this setup (5 V rail dead), so these figures exclude it.

| Quantity | Value | Note |
|---|---|---|
| Deep-sleep floor | **~25.1 µA** (24.5-26 µA band) | +9.3 µA vs the 15.8 µA DESPI-gated baseline; ≈0.8 C/day. DESPI-C02 ungated is ~534 µA |
| Full refresh event | 12.21 mC over 3.57 s, 43.3 mA peak | first I6FD datapoint, panel-specific; reclassified as wake+refresh on 2026-07-26 |
| One refresh/hour | ≈3.4 µA-equivalent | |

The ±0.7 µA fuzz on the floor at 100 ksps is normal PPK2 low-range noise; the
average is the figure. Evidence:
`xiao-seeed-esp32c6-seeed-epd-board-GDEW029I6FD-screen-refresh.png`,
`-deep-sleep-floor.png`, `-1min-overview.png`.

## Seeed XIAO ePaper Driver Board, battery path via the shield JST (2026-07-05)

The ETA9740 path idles at ~330-500 µA, ~20× the rest of the system. Ruled out
for deployment; go battery-direct on the XIAO BAT pads.

Conditions: same rig, PPK2 as battery into the shield's JST, two runs at 3.3 V
and 4.2 V.

| Quantity | 3.3 V | 4.2 V |
|---|---|---|
| Floor | **~499 µA** avg, settling from ~900 µA after plug-in | ~483 µA over the first minute, settling to ~327 µA in the second |
| Idle signature | 20-83 mA pulses every ~2 s (load-detect / boost refresh) over continuous pulse-skipping fuzz | 900 µA at connect; fuzz stops ~t+65 s; then bursts every ~2-5 s, some with ~100 mA restart inrush |
| Wake+refresh at the battery node | 17.13 mC / 3.24 s = 56.5 mJ | 12.31 mC / 3.34 s = 51.7 mJ |
| Same event at the 3V3 rail | 12.21 mC = 40.3 mJ | |
| Double-conversion efficiency (boost → 5 V → XIAO LDO) | ~75-80%, net of ~5.3 mJ ETA9740 idle in the window | ~78% |

The sleeping system sits below the ETA9740's load threshold, so it pulses
forever. Settled, 327 µA is ~7.9 mAh/day; at 499 µA a 400 mAh pouch drains in
about a month. The 4.2 V settling coincides with the first LP-core wake at
~60 s but is the IC's own standby transition; a µA-scale LP read cannot lower
the boost duty. Compare refreshes in mJ: the 12.31 mC at 4.2 V matching the
rail's 12.21 mC is the higher voltage compensating. Evidence:
`xiao-seeed-esp32c6-seeed-epd-board-GDEW029I6FD-eta9740-battery-path-floor.png`,
`-eta9740-battery-path-refresh.png`,
`xiao-seeed-esp32c6-seeed-epd-board-GDEW029I6FD-eta9740-4V2-settling.png`,
`-eta9740-4V2-settled-floor.png`, `-eta9740-4V2-refresh.png`.

## XIAO C6 battery-direct on the BAT pads, voltage sweep (2026-07-05)

Floor 22.0 µA / 92 µW at 4.2 V; the usable window ends at ~3.6-3.7 V. The buck
regulates cleanly down to 3.7 V, sags between 3.65 and 3.55 V, and its deep-sag
comparator edge is at 3.545 ± 0.005 V.

Conditions: same rig, PPK2 as battery on the XIAO's underside BAT pads, shield
JST empty, switch off. From the XIAO C6 v1.0 schematic
(`hardware/XIAO ESP32-C6 v1.0 SCH.pdf`): the 3.3 V rail is a SGM6029C
synchronous buck (0.47 µH), not an LDO; VBAT feeds it through a LP0404N3 P-FET
power path, VBUS through a Schottky; the charger is a separate SGM40567-4.2
(120 mA).

| VIN | Floor | Input power | Regime |
|---|---|---|---|
| 4.2 V | **22.0 µA** | 92.4 µW | healthy PSM: clean PFM, sparse 2-8 mA narrow spikes |
| 3.9 V | 22.9 µA | 89 µW | healthy PSM |
| 3.8 V | 24.3 µA | 92.3 µW | healthy PSM |
| 3.7 V | 22.9 µA | 85 µW | healthy PSM, lowest verified-good point |
| 3.6 V | 19.2 µA | 69 µW | sag band: quiet phase plus recovery storms to 0.53 A |
| 3.5 V | 10.75 µA | 37.6 µW | deep sag plus 0.88 A storms, reproduced twice |
| 3.4 V | 26.2 µA | 89 µW | continuous-burst dropout: dense 5-13 mA µs spikes, rail held, functional |
| 3.3 V | 121 µA | 400 µW | ~30 Hz sag/burst sawtooth to 480 µA, system alive |
| 3.2 V | 304 µA | 970 µW | 0.54 A boot-loop on entry, then dead; flat converter churn (max 320 µA, no LP spikes) |

10 mV bisect of the sag edge (short captures, floors stable):

| VIN | 3.51 V | 3.52 V | 3.53 V | 3.54 V | 3.55 V |
|---|---|---|---|---|---|
| Floor | 7.98 µA | 6.89 µA | 7.91 µA | 8.07 µA | 25.13 µA |
| Power | ~24-29 µW deep sag | | | | 89 µW, regulating |

Rail power is 82.9 µW, so the healthy points show ~90% buck efficiency at a
25 µA load; battery current is lower than rail current. 3.55 V still showed one
storm in a minute and 3.6 V dwells intermittently sagged, so ~3.55-3.65 V is a
bistable hysteresis band. ETA9740 leakage in this configuration: none observed;
the 22 µA floor matches the rail baseline within buck efficiency. Evidence:
`xiao-c6-bat-pads-4V2-floor.png`, `-4V2-floor-zoom.png`, `-3V9-floor-after-boot.png`,
`-3V8-floor.png`, `xiao-c6-bat-pads-3V7-clean-floor.png`, `-3V6-sag-with-storm.png`,
`-3V5-sag-and-burst-storm.png`, `-3V4-continuous-burst.png`,
`-3V3-dropout-sawtooth.png`, `-3V3-dropout-sawtooth-zoom.png`,
`-3V2-bootloop-then-dead.png`.

Open:
- the 3V3 rail was not probed during the 3.5 V quiet phase; the sag is inferred
  from input power below the sleeping load.

## XIAO C6 buck sag: mechanism and shutdown thresholds (2026-07-05)

C6 shutdown raised 3650 → 3700 mV and warn 3750 → 3800 mV (`431ea30`); the
cost is ~12-15% of pack capacity by OCV instead of the 5-8% a 3.6 V cutoff
would strand.

Mechanism: the SGM6029's NMOS high-side needs a bootstrap cap that recharges
only when the low-side switches. Near VIN ≈ VOUT the hysteretic mode logic
barely switches, the bootstrap starves and the high-side degenerates to a
source follower (VOUT ≈ VIN − VTH, ~2.9-3.1 V). A sagged rail lowers the
sleeping load (leakage falls with VDD), which is why sag-band input power
reads below healthy. Deep sleep tolerates it; a wake demanding tens of mA
collapses the follower into brownout restart storms at the current limit
(di/dt ≈ VIN / 0.47 µH ≈ 7 A/µs, 0.5-0.9 A combs). At 3.4 V the 97% duty
demand forces continuous bursting, each burst refreshing the bootstrap, so it
is loud but healthy (89 µW). At ≤3.3 V conversion is impossible. The comparator
edge at 3.545 V ≈ VOUT + 245 mV is the "VIN close to VOUT" mode detector.

| Item | Value |
|---|---|
| Datasheet claim | 100% duty-cycle operation, VIN 1.95-5.5 V, UVLO ~1.9 V, no VIN > VOUT margin stated; 3.8 V appears only as a plot condition |
| Datasheet Iq | 2.3 µA not switching / ~8.5 µA switching PSM, bracketing the measured floors |
| Cutoff cost at 3.6 V (not chosen) | ~20-30 mAh of 400 mAh (~4-7% energy, ~3-6 weeks of a ~1.5 yr life); LCO LiPo OCV stays ≥3.6 V to ~5-8% SoC |
| Cutoff cost at 3.7 V (chosen) | ~12-15% by OCV |
| Sag at µA load | C/18000 floor, ~0.11C refresh peaks, ~10-20 mV; VBAT rides the OCV curve |
| LiFePO4 (3.2 V nominal) | unusable, whole curve below the cliff |

Cold raises ESR several-fold, so sample VBAT during sleep, not mid-refresh: a
45 mA refresh at ~0 °C sags below threshold early. Firmware at the time:
`read_battery_level()` stubbed (returns 4321) and thresholds 3200/3000 mV sat
below the misbehaviour; the thresholds are done, the stub survives. No header
pin is free for a divider with the shield fitted; the underside MTMS/MTDI pads
are ADC-capable (`docs/wiring.md`).

## Flash history archive: base snapshot cost, ESP32-E (2026-07-25)

A base snapshot costs 7.14 mC over 170.2 ms; at the ~1/day cadence that is
0.1% of this rig's ~7.1 C/day.

Conditions: FireBeetle 2 ESP32-E + BMP390L + GDEH0154Z90, PPK2 source meter
3300 mV, `dfrobot_firebeetle2_esp32e_debug` with
`-DPPK2_DEBUG -DHISTORY_BASE_EVERY_WAKE` (one snapshot per wake; normal cadence
is ~1/day). Non-refresh wake, panel rail already gated by `epd_power_off()`.
The write is bracketed on D1 by a 3×50 ms preamble.

| Quantity | Value |
|---|---|
| Duration | 170.2 ms |
| Average current | 41.94 mA (46.83 mA peak), ~29 mA baseline during the preamble |
| Charge | **7.14 mC** (23.6 mJ at 3.3 V): 2.2 mC flash, 4.9 mC the awake time it forces |
| On-device timing (`ms_now()`) | erase 104-125 ms, program 25 ms, verify 7-8 ms; the ~13 ms remainder is CRC32 over the 6.4 KB payload plus malloc/memcpy |
| Erase-time drift | 104 → 117 → 125 ms over ~75 snapshots on two ping-ponged sectors (~37 cycles each); a 20% spread on the dominant term |
| Journal append | ~1 ms, not separately resolvable |

| Base snapshot cadence | Cost | Share of ~7.1 C/day (1.68 C floor + ~48 refreshes × 112 mC) |
|---|---|---|
| ~1/day (current) | 7.1 mC/day | 0.1% |
| hourly | 171 mC/day | 2.4% |
| every wake (~72/day) | 514 mC/day | 7.2% |

Flash the forcing build back out after the capture: at a 5 s interval in the
USB service window it is ~8,600 erases per base slot per day against a 100k
cycle NOR figure, so a slot is spent in under a fortnight (derived from the
layout; the flash part is not identified in this repo). Hourly snapshots would
keep the 24h sparkline no more than an hour stale after a reflash for 2.4%;
not taken, the sparkline rolls over daily anyway.

Open:
- the erase-time drift, if it keeps climbing (temperature or noise more likely
  than wear at ~37 cycles).

## Base snapshot: overlap and duration options (considered 2026-07-25)

Neither overlapping the snapshot with other work nor shrinking it was taken.

- No parallelism exists: `esp_flash_erase/write` disable the cache and busy-poll
  the status register; IDF has no async or DMA flash API.
- The EPD busy-wait is light sleep at ~1-2 mA (a ~20 s Z90 refresh averages
  ~5.6 mA). Writing flash there means staying awake: ~27 mA × 170 ms ≈ 4.7 mC
  added against ~4.9 mC saved, and a cache-disabled 125 ms erase mid-waveform
  risks the corrupted frame `epd_pin_sleep_hold()` exists to prevent.
- The SNTP wait is idle-awake but comes before the drift block the snapshot
  must capture.
- Duration lever: the 6388 B payload spans two 4 KB sectors. Dropping the
  hourly ring (4320 B) from the base leaves ~2 KB, one sector: erase ~53 ms,
  total ~76 ms, ~3.2 mC (−55%). Not done: it saves 4 mC/day of ~7.1 C/day,
  restore would have to walk the journal backwards across base generations
  (the `base_seq` filter only works forwards), and the base could no longer
  restore 30 days alone if the journal were damaged. Revisit if hourly.

## C6 ePaper rig: measured budget (2026-07-26)

2.12 C/day, ~680 days on a 400 mAh pack, with every term but one measured on
this rig.

Conditions: XIAO C6 + BMP581 + Seeed ePaper driver board (GDEW029I6FD), PPK2
source meter 4.2 V on the XIAO's soldered BAT pads, `91f08eb`
`seeed_xiao_esp32c6_epaper_release`, no `PPK2_DEBUG`, analysed with
`tools/ppk2.py`. Supersedes the projection that scaled FireBeetle numbers.

| Term | C/day | Share | Basis |
|---|---|---|---|
| Sleep floor, 21.7 µA | 1.875 | 86% | measured, flat over 21 min |
| Refresh wakes, 10.7/day × 10.05 mC | 0.107 | 4.9% | both measured |
| NTP resync, 117 mC / 1.54 d | 0.076 | 3.5% | both measured |
| Non-refresh wakes, 20/day × ~2.5 mC | 0.051 | 2.3% | rate measured, charge estimated |
| Post-wake transient, 0.26 mC × 31/day | 0.008 | 0.4% | measured |
| Total | **2.12** | | ~680 days on 400 mAh |

| Figure | Value | n / window / source |
|---|---|---|
| Sleep floor | 21.7 µA | 1200 s `--from/--to` window 21.72 µA; 60 s bins 21.5-22.1 µA over 21 consecutive min; field interval ~46 min |
| Wake + refresh | 10.05 mC / 3.25 s | n=4 production: 9.62, 9.53, 10.43, 10.62 (±6%) |
| Panel refresh alone | ~8.3 mC / 3.03-3.06 s | n=5, 7.56-9.23 mC (±10%), D1-bracketed on a `PPK2_DEBUG` build; ~5 mC of wake overhead. The 12.21 / 12.31 mC figures of 2026-07-05 were wake+refresh |
| Successful NTP resync | ~117 mC / 1.8 s | two acquisition paths 6% apart: 113.4 mC live via `ppk2-api`, 120.7 mC from an nRF CSV export; 198 mA spike, 70-80 mA for 1.3 s, two TX bursts. 2-3× cheaper than the 200-400 mC projected |
| Post-wake transient | ~0.26 mC per wake | peaks ~20 s after wake, decays over 35-60 s; ~40% duty at 60 s bench wakes, hence 28-35 µA bench means |
| Refresh rate | 10.8/day | 216 refreshes over 19d23h, basement at 21.5-24.5 °C; delta-triggered, so 10-50/day is the operating range (E rig 48/day) |
| Wakes | ~20 non-refresh CPU wakes/day, 31 total | same run |
| Resync interval | ~1.5 days | see note |
| One-time archive format | ~2.2 s / ~76 mC | differenced from two boots that also differed in firmware; a 1.7 s full-chip erase implied single-digit seconds against the ~26 s sector-rate projection |
| Base snapshot, no-erase case | 0.54-0.73 mC / 24 ms | freshly formatted archive; the E's 170 ms / 7.14 mC is erase-bound |

Resync interval note: the C6's RC drift read +452 ppm off a forced-refresh
panel at the time; the rig's own journal later gave +305 ppm (2026-08-05) with
the interval hunting a 1.7-3.5 d band (`docs/clock-drift.md`). Failed attempts
re-armed with no backoff, pinning a no-WiFi board at 1 day; fixed 2026-08-09
(`2fccb5f`) for the absent-network case. The stock RC already buys ~1.5 days,
which weakens the quantitative case for the FC-135 on `thermometer_c6`.

Marker-bounded wake figures here are lower bounds: `CPU_ACTIVE` misses the ROM
and IDF preamble (~45 ms unmarked as of `f07d2c9`, 445 ms before it). Short
windows holding different fractions of the post-wake transient read
26/48/52/76/141 µA on this rig; only the whole-cycle averages above count.
Debug-build figures (`PPK2_DEBUG`, +4-6 mC per wake) compare only with
debug-build figures. Reading rules: `/device-session`.

Open (2026-07-26, XIAO rigs):
- non-refresh CPU wake charge (the 2.3% estimate; every captured wake refreshed);
- failed resync charge on the C6: 1.5 C (association timeout) and 4.5 C (plus
  SNTP timeout) are ESP32-E figures assumed to transfer;
- journal append (~0.04 mC assumed) and ring sector erase (~2 mC assumed, once
  per ~10 days), never measured on either board;
- on the 920x680 panel: `! NOARCH` legibility in FreeSans12pt7b, and whether a
  `HOURLY_NO_DATA` gap reads as a gap rather than a dotted line.

## thermometer-c6 rev A board 1: first sleep floor (2026-07-29)

Floor 18.6-18.8 µA at 4.2 V through the deployment path, ~3 µA under the XIAO
ePaper rig at the same node.

Conditions: board 1 + BMP581 (U5) + GDEM0154I61 in J4, PPK2 source meter
4.2 V into J1 through the Dupont-into-JST harness (Q6 and the MCP73831 VBAT-pin
leakage inside the measurement), `cbda104` `thermometer_c6_release`, no
`PPK2_DEBUG`, LEDs enabled (wake blinks are the only observability without
serial), ambient ~27 °C with the board still shedding USB-era heat (BMP581
~30 °C). 149 s capture, `local/captures/ppk-20260729T141836.csv`, `tools/ppk2.py`.

| Quantity | Value | n / window |
|---|---|---|
| Sleep floor | **18.6-18.8 µA** | `--from/--to`: 58 s → 18.8, 56 s → 18.6; 5 s bins 18.9 → 18.6 µA over 2.5 min (raw band 17.5-20.2 µA); longest quiet window 59.75 s |
| Floor alone | ~1.62 C/day | |
| Wake + refresh | 23.40 / 23.46 mC over 2.75 s | n=2 |
| Bench cadence | one wake per 60 s | every LP poll delta-fired while the board cooled |

The ~0.3 µA downward drift is the board cooling (leakage falls with
temperature), 100× smaller than the XIAO rig's post-wake transient. The older
15.8 µA C6 figure is not a comparator: it was sourced at 3.3 V into the 3V3
rail with the input tree bypassed (15.8 load + ~2 RT9080 Iq + ~1 Q6, charger
and D2 leakage ≈ 18.7). The refresh is not comparable to the XIAO's 10.05 mC:
different panel (I61 vs I6FD), LEDs on, and an LDO reads ~1.15× a buck's input
charge at 4.2 V. Power-saving state at capture: `EPD_POWER_GATE`,
`CONFIG_BOOTLOADER_SKIP_VALIDATE_IN_DEEP_SLEEP=y`, `DISABLE_SERIAL`, high-side
gated VBAT divider (ungated would add ~5 µA). Every NTP attempt succeeded
(a dozen-plus cold boots, two builds, zero failures) where the XIAO rigs see
periodic association and SNTP failures; consistent with the MINI-1 PCB antenna
over the ceramic chip antenna, same bench, small n. Failed resyncs are the
budget's expensive tail (1.5-4.5 C each, no backoff at the time).

Open:
- anything about the ~46 min field interval is extrapolation from 59.75 s;
- marker-separated wake decomposition (Phase 3).

## thermometer-c6 rev A board 1: hour-long capture (2026-07-29 evening)

Settled floor 18.3 µA over a full field interval; LP poll ~4 µC; first C6
non-refresh CPU wake measured at 7.74 mC.

Conditions: same rig and build, 1000 S/s, 4200 mV,
`local/captures/ppk-20260729T153004.csv`. Forced refresh at the 55 min mark
read `#8 r7 lp55 0d w:ULP mx:4.2V cbda104`, 4176 mV (−24 mV, second ADC point).

| Quantity | Value | n / window |
|---|---|---|
| Sleep floor | **18.3 µA** including LP polls, ~18.2 µA between them | longest quiet window 2397 s ≈ the ~46 min field interval; flat after ~6 min |
| LP poll | ~4 µC: 3.96 µC over 8 ms, 494 µA avg, 1.11 mA peak | 1 s bins on the 60 s grid (t ≡ 24 mod 60) read 22.1 vs 18.3 µA, ~40 occurrences; one direct UI selection |
| LP poll, equivalent | +0.06 µA at 60 s cadence, +0.8 µA at the 5 s debug cadence | `lp55` at 55 min: every poll survived, no `uN` |
| Non-refresh CPU wake | **7.74 mC / 0.50 s** | n=1, LEDs on |
| Wake + refresh | 23.8-24.6 mC | n=8, drifting down as the board settled |
| Boot + resync | 552 mC / 19.2 s | vs 282 mC / 9.5 s at the first release boot; WiFi variance |
| Unexplained | 20.33 µA over the 57 s after the third refresh (t=206-264) | single occurrence, ~2 µA above neighbours |

The poll is ~2000× smaller than a CPU wake, a different event class. Against the
XIAO's ~3 µC / 3 ms at ~1 mA (2026-04-21, Arduino era, shape estimate): same
amplitude, ~30% more charge, 3 → 8 ms, plausibly the espidf migration and July
LP hardening (counter carry-over, identity checks) adding I2C traffic;
+0.02 µA at 60 s, cosmetic. The non-refresh wake is 3× the ~2.5 mC the XIAO
budgets carry; LEDs and the LDO's ~1.15× factor inflate it, LED share
unquantified. Rough budget: 1.58 C/day floor + 0.24-1.22 C/day for 10-50
refreshes × 24.3 mC ≈ 1.8-2.8 C/day, ~500-800 days on 400 mAh.

## Budget as measured 2026-07-29 (thermometer-c6 board 1)

~2.0 C/day at a quiet cadence, ~3.0 volatile; 480-710 days on 400 mAh at full
capacity, LEDs enabled.

Charges measured on this board; cadences from the XIAO runs, since a
delta-driven cadence measures the room.

| Term | C/day | Share (stable) | Basis |
|---|---|---|---|
| Sleep floor, 18.3 µA (incl. LP polls @60 s) | 1.58 | ~78% | measured, flat over a full field interval, 27 °C |
| Refreshes, 10.8-50/day × 24.3 mC | 0.26-1.22 | 13% | charge measured n=8; cadence = the room (XIAO basement nominal, E heatwave ceiling) |
| Non-refresh CPU wakes, ~20/day × 7.74 mC | 0.15 | 8% | charge measured n=1; rate from the XIAO 20-day run |
| NTP resync | 0.02-0.08 | 1-4% | 117 mC/success (XIAO-measured); interval pending this board's crystal drift, 1.5 d → weeks |
| Archive (journal + base + ring erase) | ~0.005 | <1% | mixed measured/estimated, noise-level |
| Total | **~2.0 stable → ~3.0 volatile** | | ~480-710 days on 400 mAh |

Same ballpark as the XIAO ePaper rig's 2.12 C/day despite the 16% better
floor: the wake tiers are higher here (LEDs in every wake figure, the LDO's
~1.15× factor, the non-refresh term tripling once measured). The crystal's
resync dividend is not yet counted. Caveats: pack self-discharge at 1-2%/month
on a 400 mAh pouch is 0.5-1.0 C/day equivalent, not in the table. The 3800/3700
mV thresholds were buck-era and stranded ~25% of capacity; replaced 2026-07-31
(`1e1048e`) by 3550/3500 mV after the BOD probe measured ~300 mV droop at the
refresh peak (the XIAO keeps 3800/3700). Net: roughly 1.5-2 years on 400 mAh.

Open:
- LED share: re-measure one refresh and one non-refresh wake with `DISABLE_LEDS`;
- warm floor (D2 leakage vs temperature) and failed-resync tails.

## thermometer-c6 board 1: sleep floor with the VBUS wake armed (2026-07-30)

No measurable cost from the armed GPIO4 VBUS wake: the floor tracks the
hour-long run to 0.04 µA at matched elapsed time.

Conditions: same rig, PPK2 4.2 V into J1, battery and USB out, `497024a`
`thermometer_c6_release`, no `PPK2_DEBUG`, LEDs enabled. Capture
`ppk-20260730T184218.csv`, 440 s, not retained (lived in `/tmp`). Under test:
the USB service window arms a GPIO wake on the VBUS divider (GPIO4) at every
sleep entry with VBUS low, via
`esp_sleep_enable_gpio_wakeup_on_hp_periph_powerdown()`.

| Quantity | Value |
|---|---|
| Seven consecutive 57-60 s windows | 19.06 → 18.72 → 18.62 → 18.56 → 18.45 → 18.39 → **18.35 µA**, still falling at 440 s |
| Comparator | 18.3 µA settled (hour-long run, `dc426ed`); 18.35 µA at t=374 s here vs 18.31 µA at t=387 s there |
| Wakes | 2.749 s / 26.4-26.6 mC, vs 23.8-24.6 mC for the same 2.75 s in the hour-long run |

This capture never settled (the hour-long run needed ~6 min to flatten, then
held 18.31 µA for 40 min), so it cannot bound the cost below ~0.1 µA; a B-A-B
interleave with `-DDISABLE_USB_WINDOW` was not run.

Open:
- the ~8% wake-charge excess at identical duration; the board was hotter, just
  off a USB session. Not in any budget.

## thermometer-c6 board 1: battery-floor voltage sweep at J1 (2026-07-30)

The fresh-boot cliff is at 3317-3320 mV and ≤1-2 mV wide; the healthy floor
rises ~3.5 µA per volt of VIN drop and knees at 3.34 V.

Conditions: first run of `tools/ppk2.py sweep --rail reva-j1` (fresh
power-cycled boot per step, regime classified from current alone, automatic
bisect). Board 1 + BMP581 + GDEM0154I61, PPK2 source meter at J1 through the
JST harness, battery and USB out, `1d567b6` `thermometer_c6_debug` with
`PLATFORMIO_BUILD_FLAGS="-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI"` (5 s LP
polls as liveness heartbeat, 3700 mV latch disabled, no NTP so nothing reaches
the archive). 30 s dwell (below the ≥60 s the XIAO storm statistics needed:
zero storms seen, absence unproven), 20 s boot window, ambient not recorded.
Artifacts `local/sweeps/ppk2-sweep-20260730-214824/`, `-220452/` (edge hunts,
raws kept) and `-224515/` (10-step gap fill; raws deleted 2026-08-05, not
recoverable); all keep `report.md` and the per-step JSON. DEAD labels in the
first two reports predate the `ee0a8d0` relabel; read them as DEGRADED.

| VIN | Floor | Input power | Regime (fresh boot) |
|---|---|---|---|
| 4.20 V | **18.97-18.99 µA** | 80 µW | healthy; raw peak 667-673 mA is first-power inrush, matching Phase 1's 0.67 A |
| 4.10 V | 19.23 µA | 79 µW | healthy |
| 4.00 V | 19.45 µA | 78 µW | healthy |
| 3.90 V | 19.73 µA | 77 µW | healthy |
| 3.80 V | 20.01 µA | 76 µW | healthy |
| 3.70 V | 20.28 µA | 75 µW | healthy |
| 3.60 V | 20.61-20.63 µA | 74 µW | healthy |
| 3.55 V | 20.81 µA | 74 µW | healthy |
| 3.50 V | 21.05 µA | 74 µW | healthy |
| 3.45 V | 21.28 µA | 73 µW | healthy |
| 3.40 V | 21.75 µA | 74 µW | healthy |
| 3.38 V | 22.01 µA | 74 µW | healthy |
| 3.34 V | 23.74 µA | 79 µW | healthy, first departure from the linear trend |
| 3.32 V | 29.5-29.8 µA | ~99 µW | healthy, floor +30% |
| 3.31 V | 103-105 µA | ~343 µW | boots and renders, then sleep breaks: ~55 Hz small events over ~104 µA |
| 3.00 V | 1213 µA | 3639 µW | continuous churn through the boot window, no liveness |

| Finding | Value |
|---|---|
| Healthy trend | 18.99 → 22.01 µA over 4.2 → 3.38 V, input power 74-80 µW, within ~2 µA of the published 18.7 µA over the whole deployment window; knee at 3.34 V, +30% at 3.32 V (~60 mV early warning) |
| Repeatability | 18.97/18.99 µA at 4.20 V and 20.61/20.63 µA at 3.60 V across sweeps an hour apart (~0.02 µA) |
| Cliff | run 1 (10 mV bisect): lowest healthy 3320, first unhealthy 3310, both re-run; run 2 (1 mV bisect): 3318/3317 with one bistable flip |
| Render | never failed: full refresh (56-60 mC) at every step down to 3.31 V; 3.00 V drew boot-shaped current for the whole window |
| Below the edge | ~104 µA floor with 200 µA+ sub-50 ms events at ~55 Hz; not a reset loop. Replay: `ppk2.py raw local/sweeps/ppk2-sweep-20260730-220452/step02-3317mv.bin --profile 500` |
| Debug vs release floor | 18.97 µA vs 18.3 µA: two extra ~3.96 µC polls per 10 s ≈ +0.8 µA (estimate), not a regression |

The LDO tree fails soft at 3.32 V against the XIAO buck's comparator edge at
3545 mV, ~230 mV lower; the failure mode is the sleep degrading, not the
refresh, the opposite polarity to the XIAO. Thresholds applied 2026-07-31:
3550 warn / 3500 shutdown, board-scoped in `Thermometer.cpp`, ADC-fail
fallback 3525 (the XIAO keeps 3800/3700). The candidate was 3550/3450; the BOD
probe below measured ~300 mV droop at the refresh peak, so 3500 holds ~200 mV
of rail margin over the C6's 3.0 V spec floor where 3450 would leave ~150, and
the shutdown itself is a render plus persist on a cold, sagging cell. This
reopens most of the ~25% of capacity the 3700 mV cutoff stranded (OCV estimate).

Open:
- what oscillates below the edge (RT9080 at dropout suspected; a scope on 3V3
  would say);
- cold (~0 °C) and real-cell runs decide whether the last ~5-8% (3450) is safe.

## thermometer-c6 board 1: BOD probe at SEL_2, 3V3 droop at the refresh peak (2026-07-30)

Total droop at the refresh peak ≈ 300 mV: the rail crosses a ~3.27 V trip when
VIN ≤ ~3.57 V.

Conditions: same rig and flags, `6e2fa64` `thermometer_c6_bod_probe`: the sweep
build with the brownout detector raised from 2.51 V (level 7) to ~3.27 V
(level 2, the top setting; IDF calls the level voltages estimates). A dip below
the trip during the ~425 mA EPD-boost peak is a BROWN reset, which the sweep classifier
reads as non-HEALTHY. Runs `local/sweeps/ppk2-sweep-20260730-233220/` (13 steps,
4.2 → 3.35 V plus bisect, raws kept) and `-234959/` (7-step edge re-run; raws
deleted 2026-08-05).

| VIN | Behaviour under BOD ~3.27 V |
|---|---|
| ≥ 3.60 V | HEALTHY, both runs: normal ~50 mC refresh, blips on cadence |
| 3.56-3.59 V | stochastic: bistable flips both directions across the two runs |
| ≤ 3.55 V | deterministic churn: 430-1190 mC across the full 50 s capture, zero blips |

Every churn step still shows ~430-460 mA raw peaks: each attempt survives boot
and dies at or after EPD gate-on, then retries for the whole window. The
stochastic band matches the attempt-to-attempt spread of the inrush peak
(404-511 mA). The droop is LDO dropout at the peak plus harness and connector IR
plus trip-estimate error; the split is unknown, the sum is what margin
arithmetic needs. This lands near the RT9080 datasheet worst case
(SCHEMATIC-VERIFICATION: VIN ≥ ~3.71 V to hold 3.3 V at 465 mA). At a 3450 mV
shutdown every refresh peak would pull the rail to ≈3.15 V on a stiff bench
source, ~150 mV over the C6's 3.0 V minimum, before cold and cell ESR. Release
builds keep the 2.51 V level, so deployed behaviour is unchanged. The peak
itself was later found to be a µs transient, not a load: see the 2026-08-11
board 2 sweep.

## WiFi association and DHCP timing, rev A board 2 (2026-08-09)

A connect is ~0.3 s of association plus 2.2-4.6 s of DHCP; the scan is a fixed
~2.5 s. Durations only, no PPK2 pass, so nothing here is a charge figure.

Conditions: board 2, `thermometer_c6_debug`,
`PLATFORMIO_BUILD_SRC_FLAGS="-DWIFI_SPIKE"` at `e557dd2-dirty`, USB-powered,
~2 m line of sight to the AP, target on channel 6 at −53..−58 dBm. Throwaway
`src/WifiSpike.cpp` harness, since deleted.

| `scan_time.active.max` | Duration | APs seen |
|---|---|---|
| 120 ms (IDF default) | **2501 ms** (n=8, zero variance) | 6-14 |
| 60 ms | 1801 ms | 5-13 |
| 40 ms | 1601 ms | 7-10 |

Fit: ~1.2 s fixed + ~11 × active.max. The 11 channels × 120 ms ≈ 1.3 s
projection was 2× optimistic. A back-to-back second scan cost the same 2500 ms,
so the fixed part is the scan's, not driver start-up. Consecutive identical
scans returned 5, 6, 7, 8, 9, 10, 12, 13 and 14 APs, so `wifi_connect()` does
not conclude "no network" from one scan.

| Phase | Duration | n |
|---|---|---|
| Association | ~300 ms (295-335), identical swept, channel-pinned or BSSID-pinned | 15 |
| First connect after boot | 900-2350 ms | 3 |
| DHCP | 2.2-4.6 s, ~90% of a ~4 s connect | |

Caching a BSSID or channel buys nothing; what is worth remembering across a
sleep is which network worked, so the 2.5 s scan can be skipped: one RTC byte.

| DHCP change | DHCP mean | Verdict |
|---|---|---|
| baseline | 3920 ms (n=8, 3323-4619) | |
| `CONFIG_LWIP_DHCP_DOES_NOT_CHECK_OFFERED_IP=y` | **2841 ms** (n=9, 2280-3386) | −1.08 s, taken (`62320af`) |
| `CONFIG_LWIP_DHCP_RESTORE_LAST_IP=y` | 2727 ms (n=9) | no effect, dropped |

The ARP-check saving is a clean separation (one overlapping value), inside the
"1 - 2 seconds" the Kconfig documents. Cost of taking it: the device binds
whatever is offered, so an address in use by a host the server does not know
(a static IP inside the pool, a second DHCP server) presents as a healthy
association whose SNTP fails, a persistent `! NOSYNC` indistinguishable from a
dead AP. Suspect an IP conflict before the radio. `RESTORE_LAST_IP` also fails
on cadence: resyncs run ~1.5-28 days apart against 12-24 h leases, and RFC 2131
has the server stay silent rather than NAK an unknown client, so the client
waits out a timeout.

| IPv6 (`CONFIG_LWIP_IPV6_AUTOCONFIG=y`, dual-stack, n=9) | Mean | Range |
|---|---|---|
| link-local ready | 1.8 s | 1.3-2.5 s |
| global ready | 5.3 s | 3.3-8.6 s |
| IPv4 (DHCP) ready | 4.2 s | 3.5-4.8 s |

IPv6 won 3 of 9, all first connects of a pass. Duplicate Address Detection is
the ARP check's analogue at ~1.8 s, and the global address waits on a Router
Advertisement whose 3.3-8.6 s jitter is the router's. Not pursued.

## DHCP server stall traced to the router, rev A board 2 (2026-08-09)

The ~2 s of a connect is the house AP sitting on the REQUEST; a static lease
removes it (~2.3 s of radio-on per connect).

Conditions: same board, firmware and build throughout, only the DHCP server
changed. Traced with `CONFIG_LWIP_DEBUG`, `CONFIG_LWIP_DHCP_DEBUG`,
`CONFIG_LWIP_DEBUG_ESP_LOG` and `CONFIG_LOG_DEFAULT_LEVEL_DEBUG` (lwIP logs
under tag `lwip` at debug level), all four reverted after.

| Server | DISCOVER → OFFER | REQUEST → ACK | Total |
|---|---|---|---|
| House AP (Freebox), n=3 | 19-30 ms | **2059-2426 ms** | ~2.1-2.4 s |
| Phone hotspot, n=3 | 14-27 ms | 12-16 ms | ~30 ms |

| Lease type on the Freebox | REQUEST → ACK | Total DHCP |
|---|---|---|
| dynamic | 2059, 2067, 2309, 2426, 2541 ms | ~2.4 s |
| static (`bail statique`, Freebox OS 4.12) | **12, 13, 15, 27, 36 ms** | ~49 ms |

A factor of ~160 on one hop, repeatable to ~10 ms, with the ACK arriving inside
a retry window rather than at a boundary, so not lost frames. Connect drops from
~2.7 s (0.3 s association + 2.4 s DHCP) to ~0.35 s. At 65-80 mA of live radio
that is ~150-190 mC per resync, ~0.1 C/day at the ~1.5-day cadence, estimated
(duration × current; integrated 2026-08-11 below). Budget impact estimated the
same way at the time: healthy network −50 to −70 mC/day (~2% of the 2.12 C/day
budget), failure path ~1.5 C → ~0.2 C. The ~4 s connect is
environment-dependent, driver: the server's ACK latency; on a well-behaved
server the exchange is 30 ms and a connect ~330 ms. `RESTORE_LAST_IP` skips
only DISCOVER → OFFER (~20 ms), which is why it measured flat. Consistent with
dnsmasq (Freebox ships it, FS#18142): a `dhcp-host` entry short-circuits
address selection; the probe landing at REQUEST rather than DISCOVER means
Free's build or lease layer differs, unresolved. Every deployed board gets a
static lease.

Ruled out on hardware: `esp_wifi_set_ps(WIFI_PS_NONE)` (2426 → 2067/2059 ms,
inside the spread); `DHCP_FINE_TIMER_MSECS` (hardcoded 500 ms in `dhcp.h`, it
only sets the 500/1000/2000 ms retry backoff after the server's silence);
duplicate `espressif` hostnames (`CONFIG_LWIP_LOCAL_HOSTNAME`; five on this LAN,
disambiguated to `espressif1..4`; `.home` DNS/DHCP coupling new in Freebox
4.11.1, FS#4079 closed 2026-05-20; a unique hostname registered and changed
nothing; unique hostnames shipped anyway from `10481f7`); a server-side ARP
probe before ACK (RFC 2131 4.3.1 says servers SHOULD NOT check at ACK, dnsmasq's
`do_icmp_ping` runs only under DHCPDISCOVER; disfavoured, though the static-lease
result says something probe-shaped happens).

## Failed resyncs back off on network absence (2026-08-09)

Retry escalation requires evidence of absence: the driver's sweep finding the
SSID on no channel and a full scan seeing none of the configured networks.

A board out of range and a board with a bad link want opposite policies: the
basement deployment should become rare, the XIAO rigs failing in range on their
chip antenna are recovering. Verified on board 2: absent gives 60 s, 120 s,
then flat at 8× the interval; present-but-unusable stays flat across seven
consecutive failures. Nothing is terminal; one success clears the counter.
Estimated ~0.2-0.4 C/day settling to ~0.05 C/day on a permanently offline
board, unchanged on a flaky one (estimate; charge measured 2026-08-11 below).

## T81 waveform LUT selection under hardware SPI, rev A board 2 (2026-08-11)

The carried GxEPD2 fork drove the T81 with its ≤5 °C waveform (`0xE8`) at 26 °C;
upstream's fallback (`0xF1`) cuts panel busy time 48.4%. Durations and busy
slices only, no charge.

Conditions: board 2 + GDEH0576T81, `thermometer_c6_debug`, rig `revA-bigscreen`,
`PLATFORMIO_BUILD_SRC_FLAGS="-DREFRESH_EVERY_N_WAKES=1 -DDISPLAY_TEMP_DELTA=99"`
(exact cadence, n=21-25 in three minutes), USB-powered with a charging pack,
ambient ~26 °C.

Mechanism: `GxEPD2_576_GDEH0576T81::_Init_Full()` picks the LUT from the
controller's sensor via `_writeCommand(0x40)` then `_readData()`. The read works
only under software SPI and returns 0 under hardware SPI. The fork fell through
`if (temp <= 5) return 232` and forced `0xE8`; stock upstream guards the failed
read with `if (temp == 0) return 241`, the 20-30 °C value.

| Driver | LUT | Busy slices (sd) | Steady-state ms | n |
|---|---|---|---|---|
| fork `1509966` | `0xE8` | 445.62 (0.50) | ~3075 | 21 |
| upstream `de82887`, LUT pinned to `0xE8` (control) | `0xE8` | 442.67 (0.48) | ~3005 | 21 |
| upstream `de82887` | `0xF1` | **228.25 (0.44)** | ~1935 | 24 |

The control row agrees with the fork to 0.66% of slices, so the drop is LUT
selection, not upstream's code. Reported wall means 3098/3034/1960 ms include
the first post-reset render (~500 ms long). Every T81 refresh figure before this
date, including the ~45 mC `@3V3 rail` XIAO + DESPI-C02 row, was taken at
`0xE8` and does not carry over; charge does not scale from busy time (refresh
current is not uniform across the waveform), so no replacement is quoted until
integrated. With the read failing unconditionally the LUT is a constant 241, so
refresh duration is temperature-independent in firmware until the sensor feeds
LUT selection.

Self-heat: `_Init_Full` already forces temperature (`0xE0`=`0x02` TSFIX, then
`0xE6`), so writing the BMP581's value is write-only under hardware SPI. The
sensor read 32.57 °C against ~26 °C ambient while USB-powered with a charging
pack, +6.5 °C, which crosses the 30 °C band boundary and would select 244 where
the room wants 241. Erring warm under-drives the panel (ghosting); erring cold
is safe but slow. `vbus_present()` (`src/Thermometer.cpp:1670`) is the gate.

Open:
- equilibrium self-heat on battery with no host or charger (Phase 3).

## First power figures for the deployment configuration, rev A board 2 + T81 (2026-08-11)

Settled floor 19.05 µA `@4V2 bat`, wake+refresh 36.77 mC, non-refresh wake
7.97 mC; the cable costs nothing.

Conditions: board 2 + BMP581 + GDEH0576T81, `thermometer_c6_release`, rig
`revA-bigscreen`, `2f22620`, no build flags. PPK2 sourcing 4200 mV at J1 through
the Dupont-into-JST harness, `JP1` untouched, battery out, USB out (Q6 and the
MCP73831 VBAT-pin leakage included). No `-DPPK2_DEBUG`: `ppk2_selftest()` costs
~40 ms per boot and the archive flush a 3×50 ms D1 preamble, several percent of
a wake; `ppk2.py` used current-derived regions (~20 µA asleep vs ~16 mA awake
and ~50 mA in boot). Corrected waveform (LUT 241).

| Capture | Window | Sleep floor | Wake + refresh | Non-refresh wake | Power-on boot |
|---|---|---|---|---|---|
| 1, board still shedding USB heat | 600 s | ~21.3 µA (19.5-22.3, n=8), not settled | 35.93 mC / 2.250 s (35.76-36.15, 1.1%, n=7) | none seen | 583.0 mC / 11.751 s |
| 2, thermally settled, USB cable attached device-side | 3600 s | **19.05 µA** over 3039.7 s continuous (50.7 min) | 36.77 mC / 2.250 s (n=5) | 7.97 mC / 0.500 s (n=1, t=78 s) | 810.5 mC / 18.25 s |
| 3, cable removed | 1200 s | 19.06 µA over 919.5 s | 36.36 mC, not usable (see note) | | |

The panel refresh measured ~1.94 s the same day, so the render is ~86% of the
2.250 s wake. Every 60 s LP poll rendered except two 117.8 s sleeps: while the
room or board moves 0.1 °C per minute this rig spends 35.93 mC per minute,
~2.15 C per hour against a ~2.0 C whole-day budget on board 1, the empirical
case for rate-limiting refreshes. 583 mC to cold-boot is ~16 refreshes, paid on
true power loss only. The non-refresh wake matches board 1's 7.74 mC / 0.500 s
to 3% with `DISABLE_LEDS` here. Sleeps after a refresh read 21.3-21.5 µA against
19.0-19.2 µA elsewhere, so a floor averaged over a few post-refresh minutes
reads ~10% high. Cable on vs off: 19.05 vs 19.06 µA (0.01 µA, 0.05%), no
resolvable leak through D2 SS14 or the 66k VBUS pulldowns. Capture 3 came back
2.4% short on samples (97.6 kSps of 100; a host decode starved the serial reads,
fixed in `a28b06b`): region means survive, region charge under-reports, so its
36.36 mC is discarded and capture 2's 36.77 mC stands.

Cold boots: 583.0 mC / 11.75 s, 810.5 mC / 18.25 s, 487.8 mC / 9.50 s. The 2×
duration spread means different work each time, hypothesis WiFi NTP bootstrap
(untested); do not average them. Not in the daily budget.

## Board 1 vs board 2 floor gap (2026-08-11)

Board 1 18.3 µA, board 2 19.05 µA: 0.75 µA / 4% apart, unresolved.

Same board revision, same `thermometer_c6_release` without flags, same
`@4V2 bat` node at J1; the rig headers differ only in panel selection. Neither
figure has a concurrent temperature: board 1 is tagged 27 °C, board 2's ~26 °C
was read hours earlier on USB. Leakage is the temperature-sensitive part of a
floor this small, so the pair rules temperature neither in nor out. The captures
were not USB-heated (capture 1 discarded for that; captures 2 and 3 agree to
0.05%) and a sleeping board dissipates ~90 µW, so it sits at ambient; the +6.5
°C self-heat applies only with VBUS in, which also makes the board's own sensor
useless as an ambient reference on USB. Candidates: board-to-board spread,
ambient drift between sessions, the panel (`EPD_POWER_GATE` cuts its rail, but
24 FPC lines run to driver GPIOs and the T81 has a far larger array behind them
than the 200x200).

Open:
- floor captures on board 2 with the FPC plugged and unplugged, back to back in
  one session, with an ambient reading each. Not run (2026-08-11).

## Budget as measured 2026-08-11 (thermometer-c6 board 2 + T81, the deployment config)

~2.3 C/day at a quiet cadence, ~3.8 volatile; 380-620 days on 400 mAh at full
capacity. The deployment panel costs ~15% more per day than board 1's 200x200
at a quiet cadence and ~25% more at a busy one.

Charges measured on this board on the corrected waveform, `@4V2 bat`; cadences
transferred from the XIAO runs, not measured. Same structure as board 1's
2026-07-29 table.

| Term | C/day | Share (stable) | Basis |
|---|---|---|---|
| Sleep floor, 19.05 µA (incl. LP polls @60 s) | 1.65 | ~71% | measured, two windows (3039.7 s and 919.5 s) agreeing to 0.05%; no concurrent temperature |
| Refreshes, 10.8-50/day × 36.77 mC | 0.40-1.84 | 17% | charge measured n=5; cadence transferred |
| Non-refresh CPU wakes, ~20/day × 7.97 mC | 0.16 | 7% | charge measured n=1; rate from the XIAO 20-day run |
| NTP resync, ~150-190 mC at a ~1.5-day cadence | ~0.10 | 4% | measured 2026-08-11 (static lease 248 mC, full DHCP 399 mC) |
| Archive (journal + base + ring erase) | ~0.005 | <1% | journal append unmeasured, needs a D1 marker session |
| Total | **~2.3 stable → ~3.8 volatile** | | ~380-620 days on 400 mAh |

Against board 1's ~2.0 → ~3.0 C/day, far less than the 21× pixel count suggests:
the floor still dominates at 71% and the refresh went 24.3 → 36.77 mC. Pack
self-discharge at 1-2%/month (0.5-1.0 C/day equivalent) is not in the table. The
3550/3500 mV thresholds derived on board 1 hold: at the shipped brownout level
this board and panel measured HEALTHY at 3.50 V with the functional cliff at
~3.3 V (sweep below).

Open:
- the cold case: the second gate on 3500 vs 3450 mV is a fridge run;
- the cadence rows are transferred estimates until the soak replaces them.

## Board 2 + T81: battery-floor sweep and the boot transients (2026-08-11)

The T81 does not move the fresh-boot cliff (3320/3310 mV, same as board 1),
and the "~425-465 mA refresh peak" is a 70-330 µs capacitive transient, not a
load.

Conditions: PPK2 source at J1 (`reva-j1`), no battery, USB out,
`thermometer_c6_debug` at `ccfde51` with
`PLATFORMIO_BUILD_SRC_FLAGS="-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI"`, rig
`revA-bigscreen`, 90 s dwell, 20 s boot window, fresh power-cycle per step.
Artifacts `local/sweeps/ppk2-sweep-20260811-192621/` and the bisect re-run
`ppk2-sweep-20260811-200817` after the first died at step 11 (3200 mV) on a
tool crash (`np.bool_` not JSON-serializable; all 11 steps recovered from raw
captures via `--replay`, step 11's live raw peak lost; both tool paths fixed).

| | Board 1 + GDEM0154I61 | Board 2 + T81 |
|---|---|---|
| Raw peak @ 4.2 V | 667.4 mA | **571.4 mA** |
| Second transient | 524.3 mA | 471.9 mA |
| 1 ms-mean refresh peak | 67-155 mA | 87-138 mA |
| Fresh-boot edge | 3320/3310 mV; 3318/3317 on the finer pass | 3320/3310 mV, 3320 re-confirmed HEALTHY |

| Transient | Start | Width | Peak | Charge |
|---|---|---|---|---|
| board 2 + T81 | 2.00428 s | 330 µs | 471.9 mA | ≤ 0.16 µC |
| board 2 + T81 | 2.78669 s | 70 µs | 571.4 mA | ≤ 0.04 µC |
| board 1 + 200x200 | 2.00215 s | 300 µs | 524.3 mA | ≤ 0.16 µC |
| board 1 + 200x200 | 2.79031 s | 90 µs | 667.4 mA | ≤ 0.06 µC |

Two transients per boot at the same two timestamps on both boards and panels,
so board or firmware events, not panel events; rise inside one 10 µs sample and
exponential decay, the signature of charging a capacitance. ~0.16 µC against a
refresh's 70000 µC is invisible in any budget; sustained refresh current is the
1 ms mean, 87-138 mA. `classify_step` reports `peak_ma` as the max of the 1 ms
bin and the raw 100 kSps decimator, which keeps no timestamp. The RT9080
dropout argument in `SCHEMATIC-VERIFICATION.md` (VIN ≥ ~3.71 V at 465 mA) needs
a sustained current, and a 70 µs pulse comes from local bulk capacitance.

Below the edge: 3310 mV breaks sleep into 1906 sub-50 ms events at ~21 Hz,
3300 mV into 6892 at ~77 Hz, floor 25.9 → 45.8 → 224.5 µA across
3320/3310/3300. Refresh charge 70.25 / 70.32 / 70.54 mC over 3.287 / 3.285 /
3.285 s across the top three steps (0.4% and 0.06%), climbing to 82.5 mC by
3.3 V (constant boost power against falling input); debug-build figures (serial
live, 5 s cadence), not comparable to the 36.77 mC release baseline.

The 2026-07-30 SEL_2 BOD captures (`ppk2-sweep-20260730-233220`) show the same
two transients on both sides of that run's 3590/3580 mV edge (437-466 mA /
280 µs and 270-322 mA / 60-80 µs at 3590 HEALTHY, 3580, 3550, 3500 DEGRADED),
so the board does not die at the current peak. What changes is whole-window
charge, 84-87 mC healthy vs 458-462 mC degraded, a flat ~9.94 mA mean with
~90 mA maxima from t=4 s, `bootloops=0`: continuous churn, the same failure as
below the non-BOD edge. The shipped 3550/3500 mV thresholds stay safe and the
~300 mV droop stands as a direct measurement; its recorded mechanism does not.

Open:
- why raising the brownout level moved the edge 270 mV if the refresh peak is
  not what crosses it; a series drop between J1 and the LDO input would, and
  has never been measured. No rev B parts on this until it is.

## Board 2 + T81: BOD probe at SEL_3 (2026-08-11)

No brownout anywhere in 4.2-3.6 V with the trip at ~3.10 V; the edge is solid
at 3600 mV, bistable at 3550, dead at 3540, so droop at that point is
≈450-500 mV, 150-200 mV deeper than board 1's 200x200. The shipped 3550/3500 mV
thresholds hold.

Conditions: rail `reva-j1`, no battery, USB out, `thermometer_c6_bod_probe` at
SEL_3 (~3.10 V trip), `2541adc-dirty`,
`-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI`. Run 1
`local/sweeps/ppk2-sweep-20260811-232201/`, 11 steps as `--mv 4200,3600,3000`.
Run 2 `ppk2-sweep-20260811-235828/`, 14 steps as
`--start 3600 --stop 3000 --step 100 --confirm-edge 2`.

| VIN | Floor | Peak | Regime | Refresh |
|---|---|---|---|---|
| 4.20 V | 20.15 µA | 607 mA | HEALTHY | 65.3 mC / 3.2 s |
| 3.90 V | 20.79 µA | 496 mA | HEALTHY | 66.3 mC / 3.2 s |
| 3.75 V | 21.24 µA | 466 mA | HEALTHY | 66.8 mC / 3.2 s |
| 3.60 V | 21.64-21.79 µA | 432 mA | HEALTHY, 18/18 blips, both runs | 72.7-72.8 mC / 3.2 s |
| 3.55 V | 21.83 µA | | **bistable**: HEALTHY once in bisect, DEGRADED on both re-runs (one at 21.9 µA, 5/18 blips) | 127.6 mC / 5.5 s |
| 3.54 V | 22764 µA | | DEGRADED, no liveness | |
| 3.50 → 3.00 V | 4.8-27 mA | 465 mA at 3.00 V | DEGRADED, no liveness (3.00 V: 4799 µA, known dead regime) | |

`bootloops: 0` at all eleven steps of run 1; the refresh completed at every step
in 4.2-3.6 V (65-86 mC, 3.2-3.7 s). Run 1's reported edge (3610/3600 mV) was a
single 51.9 mA storm on a step with 17/18 blips and a completed refresh; the
same voltage re-ran HEALTHY (`anomaly: bistable`). The sparse list let that
outlier anchor the bisect, spending six probes in a range proved healthy six
times; at ~112 s per step a 100 mV descent is the cheaper protocol near an
edge, and run 2's six consecutive failing steps below the edge are what make
its result trustworthy. Floors are `thermometer_c6_bod_probe` (debug lineage),
so 20.15 µA at 4.2 V sits above the 19.05 µA release floor as expected. Droop
= VIN − 3.10 V ≈ 450-500 mV against board 1's ~300 mV (edge VIN ≈ 3.57 V, trip
3.27 V) at nearly the same input; both inherit per-chip variation of the IDF
brownout levels. SEL_2 trips at 4.23 V input, always at the render, and SEL_3
does not trip down to 3.6 V, so the rail minimum during a T81 refresh lies
between the two trip estimates. The deeper droop bites only with the detector
raised: at the shipped 2.51 V level this board and panel were HEALTHY at 3.50 V
with the functional cliff at ~3.3 V.

Open:
- refresh cost across the discharge curve: 72.7 mC / 3.2 s at 3.60 V against
  127.6 mC / 5.5 s at 3.55 V (+75% charge, +72% time for 50 mV) while still
  HEALTHY; two points, the second bistable, not a curve.

## Host-supplied LUT temperature reaches the T81 (2026-08-11)

All five reachable LUT codes select on the panel; refresh cost is a step of
~1.95× in busy time at the ≤10 °C band boundary, flat on either side.

Conditions: board 2 + T81, `thermometer_c6_debug` at `3c91183-dirty`, rig
`revA-bigscreen`,
`-DFORCE_LUT_TEMPERATURE=<C> -DREFRESH_EVERY_N_WAKES=1 -DDISPLAY_TEMP_DELTA=99`.
The force flag bypasses the VBUS gate so the check runs on USB with serial, and
raises `! LUT` on the panel. 7-19 renders per code, no faults.

| Forced | LUT code | Band | Busy slices | ms | vs 241 |
|---|---|---|---|---|---|
| −5 °C | 232 | ≤5 °C | 443 | 3012 | 1.94× |
| 8 °C | 235 | ≤10 °C | 447 | 3030 | 1.96× |
| 15 °C | 238 | ≤20 °C | 238 | 1989 | 1.04× |
| 25 °C | 241 | ≤30 °C | **228** | 1935 | 1.00× |
| 40 °C | 244 | ≤127 °C | 225 | 1925 | 0.99× |

232 and 241 match the separate-route figures of the same day (445.62 sd 0.50
and 228.25 sd 0.44). Code 242 is unreachable through `setTemperature()`: it
needs temp > 127, which `int8_t` cannot express. Warm codes (238/241/244) sit at
225-238 slices and ~1.93-1.99 s, within 6%; cold codes (232/235) at 443-447
slices and ~3.01-3.03 s. Every refresh figure recorded before this is a 241
number at ~25 °C; below the cliff 0 °C costs no more than 8 °C, so the budget
needs two numbers, not a curve. A room at ~10 °C (realistic winter for an
uninhabited location) switches between the two by the hour. Slices are not
charge: the +14% charge figure is below.

Two firmware faults found on the way, both in `Display.cpp`'s LUT plumbing
(details in git):
- the first build was a silent no-op (228 slices at a forced −5 °C):
  `Display.h` was included before `app_common.h`, so the
  `PANEL_HAS_LUT_TEMPERATURE` guard saw `USE_576_T81` undefined and both entry
  points compiled to stubs (`displays.h` documents the rule: include after
  `app_common.h`). Fixed by including `device-config.h` from
  `Display.h` plus an `#error` in `Display.cpp`; flash grew 342 B;
- the first `setTemperature()` returned early and dropped
  `_writeCommand(0x40); delay(5); _readData();` from `_InitDisplay()`, between
  `0xE9` (PST) and the `0xE0`/`0xE6`/`0xA5` LUT activation. The first refresh
  after reset worked, every later one found the panel unresponsive with BUSY
  never asserting (`DISPLAY_FAULT_BUSY_IDLE`), reproduced with battery fitted
  and USB in. Controls: `-DDISABLE_PANEL_LUT_TEMPERATURE` 20 renders / 0 faults;
  first patch at 25 or −5 °C 1 render, latched on the 2nd; corrected patch at
  −5 °C 20 / 0 at 443 slices. `_get_lut_temperature()` now differs from stock
  by three lines with an identical command sequence on the wire.

## Boost rails under the worst-case waveform, board 2 + T81 (2026-08-11)

PREVGH holds +20.031 V and PREVGL −19.380 V flat across the longest waveform
the panel produces; no sag on a 100 ms timescale. This is the evidence for the
rev B deletion of L2/R15/R16.

Conditions: board 2 + T81, `thermometer_c6_debug` at `1531d1d`,
`-DFORCE_LUT_TEMPERATURE=8 -DREFRESH_EVERY_N_WAKES=1 -DDISPLAY_TEMP_DELTA=99`
(LUT 235, ~3.03 s drive against ~1.93 s at 241). Factory bridge config JP2
0.47 Ω + JP5 10 µH, nothing reworked. UT61E+ logging at 10.1 Hz via
`dmm-tools`, black lead on GND, autorange.

| Rail | Pad | Plateau mean | Spread across refreshes | p-p within a plateau |
|---|---|---|---|---|
| PREVGH | C5 | **+20.031 V** | 20 mV (n=4) | ~200 mV |
| PREVGL | C11 | −19.380 V | 73 mV (n=5) | 183-350 mV |

PREVGH steps to +19.885 V, climbs to ~+20.08 V within ~300 ms and holds for the
remaining ~2.6 s; PREVGL does the same to −19.47 V. A pump that could not meet
the load would decay across the window. Between refreshes the rails fall away
slowly (PREVGL still at −6 to −11 V several seconds later): the gated panel and
4.7 µF discharging. The universal config delivers full, stable rails on the
deployment panel; three controller families run on it unmodified; the
datasheet pair (JP3 2.2 Ω + JP6 47 µH) is unneeded margin
(`hardware/thermometer-c6/README.md`, rev B candidates). The ~200 mV
within-plateau spread is ripple and range resolution.

Open:
- measured at PREVGH/PREVGL ahead of the panel's regulation, not VGH/VGL; C1/C2
  formally unmeasured;
- 10 Hz sees nothing under ~100 ms, so a dip at drive onset would be invisible;
- C1/C2 are 4.7 µF 25 V parts sitting near 20 V for seconds, deep into Class II
  derating, without the 50 V upgrade C17/PREVGH received in `e6828d8`.

## Cold waveform charge, board 2 + T81 (2026-08-11)

LUT 235 costs +14% charge over LUT 241, not the +95% the slice ratio or the
+57% duration scaling predicted; the cold waveform runs 1.51× longer at 24% less average current.

Conditions: PPK2 source at J1 (`reva-j1`) @4V2, no battery, USB out,
`thermometer_c6_release` at `13c231d` with
`-DFORCE_LUT_TEMPERATURE=8 -DREFRESH_EVERY_N_WAKES=1 -DDISPLAY_TEMP_DELTA=99`,
no `PPK2_DEBUG`, matching the 241 baseline's conditions (taken earlier the same
day on the same env and node, driver on its fixed fallback). 660 s,
`local/captures/reva-j1-t81-lut235.bin`.

| | LUT 241 | LUT 235 | Ratio |
|---|---|---|---|
| Wake + refresh charge | 36.77 mC (n=5) | **41.98 mC** (sd 0.48, n=7) | 1.14× |
| Wake + refresh duration | 2.250 s | 3.393 s | 1.51× |
| Average current | 16.34 mA | 12.37 mA | 0.76× |
| Busy slices | | | 1.96× |
| Wall-clock render ms | | | 1.57× |

An unheated-space deployment pays about a seventh more on the refresh term.
Busy slices repeat to 0.05% and are the sharpest detector of whether a waveform
changed, but overstate energy ~1.7×: a colder waveform is more, shorter busy
periods. Do not convert slices to power. Also from this capture: floor
19.2-19.7 µA across settled sleeps (consistent with 19.05 µA) and a cold boot
at 549.9 mC / 12.25 s, inside the 487.8-810.5 mC spread.

## WiFi resync charge, board 2 + T81, phone hotspot (2026-08-11)

First integrated WiFi figures: a plain CPU wake is 16.36 mC, a failed resync
against a known-absent AP 450 mC (0.45 C, ~3.3× cheaper than the ~1.5 C E-era timeout,
not the ~7× claimed), and an AP vanishing mid-attempt 940 mC.

Conditions: PPK2 source at J1 @4V2, no battery, `thermometer_c6_debug` at
`6a1f872` with `-DPPK2_DEBUG -DRESYNC_INTERVAL_MIN=15 -DDISABLE_DISPLAY`
(display off so the radio term is not tangled with a refresh), archive erased
first so a stored `resync_interval_s` could not defeat the override. 420 s,
`local/captures/reva-j1-wifi-hotspot.bin`. AP: a phone hotspot, the only
configured network, switched off mid-capture. Digital leads not connected,
regions current-derived.

| Event | Charge | Duration | n |
|---|---|---|---|
| Plain CPU wake, no radio | 16.36 mC (sd 0.047) | 0.75-1.0 s | 15 |
| Successful resync, cached path | 321 mC (244-422) | 4.0-8.8 s | 4 |
| Boot + scan + first resync | 506 mC | 7.50 s | 1 |
| AP vanished mid-attempt | **939.9 mC** | 33.25 s | 1 |
| Failed resync, AP known absent | 450.3 mC | ~5.9 s | 2 |

The 1.5 C baseline is an ESP32-E figure, so the ratio mixes boards. The
mid-attempt failure is twice a clean failure and 2.9× a success, the realistic
field failure, and was in no budget. After three failures there were zero
further attempts in the remaining 126 s, only 16.36 mC wakes with lengthening
sleeps: the backoff, not the per-attempt charge, bounds the cost. The success
spread (244-422 mC) is the hotspot (reason-2 and reason-205 association
retries in the serial log), so it does not transfer to the house AP.

Open:
- the AP-vanished figure is n=1; repeat before leaning on it.

## WiFi resync charge with a static DHCP lease, board 2 + T81, house AP (2026-08-11)

A successful resync on the deployment network is 248 mC with a static lease;
the full-DHCP path costs +151 mC, matching the 2026-08-09 duration estimate.
This supersedes the 117 mC / 1.8 s XIAO figure for boards behind this router.

Conditions: same board, build and rig (`cdf9365`, house AP, PPK2 @4V2 at J1);
only the Freebox lease type changed. The dynamic run took an address from the
dynamic range, so a stale lease did not equalise the runs.

| Lease | n | Charge | Duration | vs static |
|---|---|---|---|---|
| static | 10 | **248.3 mC** (sd 48.3) | 5.45 s | |
| dynamic, fast path | 5 | 277.4 mC (sd 25.4) | 5.97 s | +29 mC |
| dynamic, full DHCP | 2 | 399.0 mC | 9.00 s | +151 mC |
| cold boot | 1 each | 433.8 → 627.9 mC | 6.75 → 11.75 s | +194 mC |

The +150.7 mC and 2.25 s excess match the 2.06-2.54 s server stall traced with
lwIP debug on 2026-08-09, confirmed by integration. The +64 mC average across
all seven dynamic resyncs is a bench artifact: five were 15 s apart, so the
address was still leased to the MAC and the REQUEST was a renewal with no probe
(the 15 s override changed which DHCP path was taken, a true average of the
wrong thing). The Freebox lease is 12 hours and the cadence starts at 1.5 days
adapting toward 28 (`RESYNC_INTERVAL_MIN`/`MAX`), so a deployed board takes the
full-DHCP path effectively every time: the saving is ~150 mC per resync and the
~0.1 C/day in the budget stands. This resolves the 1.8 s vs 2.4 s contradiction
between the XIAO ePaper rig's NTP term and this network's DHCP delay: that rig
never paid the stall.

Open:
- n=2 on the expensive path: the 29% full-DHCP share could plausibly be 15% or
  50%; the naive A-vs-B difference is +63.9 mC at 2.3 sigma, and resyncs run
  sd 48 mC (19% CV) on the static arm, which is why n=10 was needed.

## Rev A discharge on battery, read at harvest (2026-08-23)

Boards 2 and 4 discharged at −2.93 and −2.92 mV/day over 11.6 days, agreeing
to 0.4%. Two-point panel readings, not curves: pack voltage is journaled
nowhere (`HistoryStore.h` has no field), and the end reading was taken before
USB went in (charger ~100 mA).

| Board | Panel | Start | End | Elapsed | Rate | Cadence |
|---|---|---|---|---|---|---|
| 2 | T81 920x680 | 3998 mV | 3964 mV | 11.62 d | **−2.93 mV/day** | 43 wakes, ~30 refreshes/day |
| 4 | T81 920x680 | 3996 mV | 3962 mV | 11.65 d | −2.92 mV/day | 43 wakes, ~30 refreshes/day |
| 1 | GDEM0154I61 200x200 | ~4200 mV assumed | 4086 mV | 23.0 d | ~−4.9 mV/day, bounded | 60.6 wakes/day |
| FireBeetle, arm 2 (2026-08-23 .. 2026-09-16) | Z90 | 4136 mV | 3688 mV | 23.7 d | −18.9 mV/day | 1440 wakes, 288 repaints/day |
| FireBeetle, arm 1 | Z90 | | | | −4.9 mV/day | 25 repaints/day, same pack |

Boards 2 and 4 sat ~10 cm apart: the first same-room discharge pair. Board 1's
soak row of 2026-07-31 records only "fully charged" and no first-render mV;
it started at the steep top of the LiPo curve where the pair started at
~4.00 V on the plateau, drives 1/21 the pixels and wakes 60.6 times a day
against 43, so it is not comparable. At the pair's rate, 3964 → 3550 mV
(`low_battery_mv`) is ~140 days, an order of magnitude from an 11-day window on
the plateau. Drift rates and the BMP581 pair comparison: `clock-drift.md`.

## Open items

One line each, with the date deferred and the rig. Closed items stay listed
with their closing entry.

| Item | Rig | Deferred | Status |
|---|---|---|---|
| Non-refresh CPU wake charge | XIAO rigs | 2026-07-26 | open on XIAO; rev A measured 7.74 / 7.97 mC (2026-07-29, 08-11) |
| Failed resync charge on the C6 | XIAO rigs | 2026-07-26 | open on XIAO; rev A 450 mC absent-AP, 940 mC AP vanished (2026-08-11) |
| Journal append (~0.04 mC assumed) and ring sector erase (~2 mC assumed) | both boards | 2026-07-26 | open; needs a D1 marker session |
| `! NOARCH` legibility and `HOURLY_NO_DATA` gap rendering on 920x680 | T81 | 2026-07-26 | open |
| Erase-time drift 104 → 125 ms | ESP32-E | 2026-07-25 | open, re-check if it climbs |
| C6 LP-core wake-latch gating | C6 | July 2026 | open, only if refresh trains appear |
| 3V3 rail during the 3.5 V quiet phase | XIAO buck | 2026-07-05 | open |
| LED share of wake charge | rev A board 1 | 2026-07-29 | open; board 2 with `DISABLE_LEDS` read 7.97 vs 7.74 mC non-refresh |
| Warm floor (D2 leakage vs temperature) | rev A | 2026-07-29 | open |
| Wake charge excess 26.4-26.6 vs 23.8-24.6 mC at equal duration | rev A board 1 | 2026-07-30 | open |
| 20.33 µA region after a refresh | rev A board 1 | 2026-07-29 | open, single occurrence |
| What oscillates below the LDO cliff (~55 Hz) | rev A | 2026-07-30 | open |
| Cold (~0 °C) run for 3500 vs 3450 mV; real-cell ESR | rev A | 2026-07-30 | open |
| Series drop J1 → LDO input (why the BOD edge moved 270 mV) | rev A | 2026-08-11 | open |
| FPC plugged/unplugged floor pair with ambient logged | rev A board 2 | 2026-08-11 | open |
| Refresh cost across the discharge curve | rev A + T81 | 2026-08-11 | open, two points |
| Self-heat equilibrium on battery (LUT gate) | rev A | 2026-08-11 | open |
| VGH/VGL at C1/C2; 25 V parts near 20 V | rev A | 2026-08-11 | open |
| AP-vanished failure, n=1 | rev A | 2026-08-11 | open |
| Full-DHCP share of deployed resyncs, n=2 | rev A | 2026-08-11 | open |
| WiFi 1: successful resync end to end, integrated | rev A | 2026-08-09 | closed 2026-08-11: 248 mC static lease, 321 mC hotspot |
| WiFi 2: resync with the AP down | rev A | 2026-08-09 | closed 2026-08-11: 450 mC, ~3.3× cheaper than the ~1.5 C E-era timeout |
| WiFi 3: one scan in isolation (2501 ms), to fix the mC per second of radio | rev A | 2026-08-09 | open |
| WiFi 4: static vs dynamic lease A/B, and the 1.8 s vs 2.4 s NTP contradiction | rev A | 2026-08-09 | closed 2026-08-11 |
| Residual ~2.7 s of DHCP after the ARP check | rev A | 2026-08-09 | closed 2026-08-09: the server's REQUEST → ACK stall |
| Connect failure modes (association timeout, weak-link retransmits) | rev A | 2026-08-09 | partly closed 2026-08-11 (absent AP, vanished AP); weak link open |
| FireBeetle E + BMP390L + Z90 at 4.2 V into the battery input via TP4056: floor over whole cycles plus one wake+refresh (its 19-20 µA / ~112 mC are rail figures; supply node unstated for July; 3300 mV once, 2026-07-25) | E | 2026-08-11 | open; gated on the rig being free of drift arms |
| XIAO C6 + DESPI-C02 + GDEH0576T81 at 4.2 V on the BAT pads (no battery figure exists; all battery-side XIAO work used the shield rig) | XIAO + T81 | 2026-08-11 | open; would also give the RT9080 rail-to-battery factor a comparator (the ~1.15× LDO factor is the reciprocal of the XIAO's ~90% buck efficiency, not a measurement) |
| Board 1 first-render mV never logged | rev A board 1 | 2026-08-23 | closed as unrecoverable |
