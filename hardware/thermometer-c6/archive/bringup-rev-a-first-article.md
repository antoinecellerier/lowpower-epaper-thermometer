# Rev A first article on board 1, 2026-07-27 .. 2026-07-29 (closed record)

**Outcome: every Phase 0–2 item closed on board 1 on 2026-07-29**, and boards
2–4 went straight to flash on the strength of that pass. Phase 3 items closed
later are recorded here with their dates. This is the record moved out of
[`../BRINGUP.md`](../BRINGUP.md), which keeps the open bench queue and the
per-board state. Figures, dates and hedges below are append-only.

## X-rays, 2026-07-27

JLC's four first-article frames, the fitted frame↔board transform and the
per-part verdicts are in
[`order-2026-07-20/xray/README.md`](order-2026-07-20/xray/README.md). J4 is
off-frame in all four images (frames cover x≲38mm of the 48mm board; J4's row
sits at x≈41.5), so the Phase 0 optical bridge check on J4 was the only
inspection it got. X-ray confirms geometry only (no bridges, nothing missing
or shifted); it proves neither electrical contact on the LGA nor passive
values, so Phases 0–2 remained the gate.

## Phase 0 — before any power (per board)

Board numbering (2026-07-29, boards in hand): the four assembled boards are
hand-marked 1–4 on the back below the USB port — the fab put no serials on
them, so the numbers map to neither JLC's internal count nor the X-ray
frames. The lone unassembled board carries a factory 0005 datamatrix and is
board 5. Board 1 is the first-article board for Phases 0–2.

- [x] Visual pass against the JLC renders / placement-verification table:
      J4 0.5mm-pitch row for bridges, U1 module fillets, U5 seated (vent
      pinhole NW, pin 1 SW), **U6 pads empty**, every diode band per the
      table (D1/D3 cathode E, D2 W, D4/D5 S, D6 W).
      2026-07-29: pass on all four assembled boards. Board 4's U5 sits
      slightly skewed (rotation). The X-rays showed all four packages
      centered, but the frame↔board mapping is unknowable, so they can't
      clear board 4 specifically; slight LGA skew is normally benign
      (reflow self-alignment). Arbitrate at the Phase 2 BMP581 detect —
      run board 4 through that check early.
- [x] Loupe + brush pass around U5: the X-rays show satellite solder
      micro-balls near the package on 2–3 boards — dislodge anything loose
      (vent-port neighborhood; harmless once confirmed not mobile).
      2026-07-29: nothing visible under the loupe on any board; finish
      very clean. Treating the micro-balls as under-package/immobile.
- [x] Jumper state as shipped: JP1 bridged (copper), JP2+JP5 bridged
      (0.47Ω RESE + 10µH — universal default), JP3/JP4/JP6 open.
      2026-07-29: confirmed on all boards. Bridges are factory copper
      (must be cut before first use as NO), matching the KiCad model.
- [x] DNP provisions empty: D7 (TVS), R9 (10M 32k bias), U6; J2/J5 headers
      unstuffed; TPs bare. C29 (10nF ADC reservoir) IS populated.
      2026-07-29: confirmed. (R9 is an 0402 across the Y1 pads — bench-
      stuff only if the 32k cold-start item bites.)
- [x] DMM resistance to GND, no dead short: VBAT, VSYS (J2.2), 3V3 (TP4),
      EPD_VCC, PREVGH, PREVGL, VCOM.
      2026-07-29: boards 1 and 5 clear on all seven rails. The RESE TP is
      *not* in this list and must not be added: TP9 sits on EPD_RESE,
      which is R14 (0.47Ω) through bridged JP2 straight to GND — board
      1's 0.60Ω there is the sense resistor plus jumper/probe resistance,
      by design. Board 5 reads open at RESE only because the bare board
      has no R14. **Boards 2–4 never got this pass, and as of 2026-08-12 they
      never will — skipped deliberately, not forgotten.** All three went
      straight to flash on the strength of board 1's pass: same reflow, all
      four X-rayed, boards 1 and 5 clear on all seven rails. What that trades
      is a dead-short check on the four gated booster rails (EPD_VCC, PREVGH,
      PREVGL, VCOM), which no boot log can cover because they are off until a
      render — but a short there fails the first refresh visibly and now raises
      the LED fault blink, so it cannot pass silently. All three have since
      rendered. Reinstate the pass for any board that is reworked or that
      arrives from a different fab run.
- [x] Diode-mode sanity (red probe = +):
      - D2 conducts **VBUS→VSYS** — anode is the east pad, cathode band
        west on VSYS (an earlier revision of this line said "VSYS→VBUS";
        that was backwards). Red on the anode pad, black on the band:
        expect a 0.2–0.35V Schottky drop.
        2026-07-29 board 1: **0.2142V forward — pass.** (The 1.96V first
        measured red-on-VSYS was the blocked direction reading through
        peripheral paths.)
      - Q6 body diode: red on J1 pin 1 (the `+` pad), black on the VBAT
        TP (bridged JP1 makes it the same node): expect ~0.4–0.7V —
        AO3401A D→S body diode, BAT_IN→VBAT_RAW. Swapped: no drop.
        2026-07-29 board 1: **0.4259V — pass** (low end is normal at a
        DMM's ~0.3mA test current; datasheet Vf figures are at 1A).
      - LP I2C pull-ups: Ω mode straight across R10 and R11 (or from
        U6's empty SDA/SCL pads to the 3V3 TP): ~4.7k each.
        2026-07-29 board 1: **4.67kΩ both — pass** (nominal −0.6%,
        within the 1% tolerance). Consistent with the earlier matched
        1.4849V diode-mode readings (≈316µA test current × 4.7k).
- [x] J4↔panel adapter pin-1 continuity (mouth EAST, pin 1 at the NORTH end
      of the row) — the respun footprint's first physical verification.
      Method: J4's nets are probeable at back TPs (GDR→2, RESE→3,
      EPD_VCC→15/16, PREVGH→21, PREVGL→23, VCOM→24, GND→8/17) or at
      front-side component pads on the same nets. Seat the rig's 24-pin
      FFC in J4 with the panel NOT attached at the far end, then beep
      each net against the adapter's matching pin. RESE (pin 3, north
      end) plus VCOM (pin 24, south end) is an asymmetric pair that
      catches a flipped row immediately.
      2026-07-29 board 1: **all continuous and on the right adapter
      pins** — RESE, GDR, GND ×2, EPD_VCC ×2, PREVGH, PREVGL, VCOM.
      The respun footprint (pin 1 north, mouth east) is verified on
      hardware. Bench note: back TPs are impractical when the reference
      is on the front face (FFC seated topside) — coordinating probes on
      both faces mid-air doesn't work; front component pads on the same
      nets were used instead. TPs remain fine for single-face probing
      (powered floor/scope work with the board face-down or on edge).
- [x] **JST pigtail polarity vs the `+` silk before first battery plug**
      (JST vs Adafruit pigtail convention differs — README open item 5).
      2026-07-29: confirmed by DMM on the loose plug — the red wire /
      + contact mates with J1's `+`-marked pad. Shell orientation also
      matches the existing devices' pigtails.

**Phase 0 complete on board 1 (2026-07-29).**

**Board 2 skipped the pre-flash steps entirely, deliberately** — board 1 had
passed cleanly, so the first article was taken as evidence for the batch rather
than each board being re-proven. It worked on first power and has been the bench
board since (2026-08-05 and 2026-08-09, `docs/history-store-validation.md`).
That is the precedent for boards 3–4: a clean first article earns the rest of
the batch a straight-to-flash.

**Board 4 is the exception to that.** Its U5 placement skew was flagged at
X-ray, which is exactly the kind of per-board defect the first article cannot
speak for — run it through the Phase 2 BMP581 detect early rather than
discovering it as a sensor fault later.

## Phase 1 — first power (battery + panel absent)

- [x] Power via PPK2 source mode, 4.0V. Injection point options:
      (a) J2 pin 2 + GND with JP1 cut open (factory copper bridge, per
      Phase 0 — knife cut, re-close with solder afterwards; "wick"
      doesn't apply the first time) — excludes Q6 and the charger;
      (b) **chosen for board 1: J1 via a Dupont-into-JST harness, JP1
      untouched** — the real battery path, so Q6 reverse-protects a
      mis-wired lead and all measurements are true battery-terminal
      figures. Includes Q6's Rds(on) (negligible at these currents) and
      the MCP73831 VBAT-pin leakage (sub-µA to low-µA, datasheet,
      unmeasured) — the Phase 2 floor read here is the deployment
      number, marginally above what (a) would show.
      A current-limited bench supply (4.0V / 50mA) at either point is
      the no-PPK2 fallback.
      2026-07-29 board 1: **first power clean** via (b). Inrush 0.67A
      for ~1–2ms (cap bank through Q6 + harness), ~10ms near zero (POR
      hold-off), then steady ROM draw — no brownout looping.
- [x] 3V3 = 3.30V at TP4 (probe only).
      2026-07-29 board 1: **3.299V — pass.**
- [x] EPD_VCC ≈ 0V (gate held off by the 10k pull-up). The node floats
      behind the off PFET — no bleed path — so a 10MΩ DMM reads the
      leakage equilibrium, not a hard 0V: a few hundred mV is a pass
      (tens of nA); ~3.3V would mean the gate is on.
      2026-07-29 board 1: **0.22V — pass** (~22nA into the DMM).
- [x] Quiescent draw plausible (unflashed module executes ROM console — mA
      range is normal; the µA floor is checked in Phase 2 after flashing).
      2026-07-29 board 1: **~22mA steady** (sel. avg 22.22mA, max
      24.38mA over 2.4s) — pass.
- [x] USB attach, battery absent: USB-Serial-JTAG enumerates; VSYS ≈ VBUS
      minus the D2 drop (load-share path). Expect the CHG LED to
      float-cycle with no battery — brief check only, then unplug (the
      product rule is: don't leave USB attached without a battery).
      2026-07-29 board 1: **all pass.** Enumerates as Espressif USB JTAG
      serial debug unit, MAC 98:88:E0:75:47:9C (board 1's identity);
      ROM banner clean over devserial (`boot:0x38` normal straps,
      `invalid header: 0xffffffff` = factory-blank flash). VSYS 4.788V
      at D2's cathode pad (≈ VBUS − 0.21V). CHG blinked once then quiet:
      VBAT (J2.2) float-holds at 4.296V — the charger topped the
      unloaded cap bank past termination (mild overshoot; Q1 blocks both
      ways with VBUS on its gate, divider gated off, so nothing bleeds
      the node back below the recharge threshold). Charger provisionally
      working; real verdict at the battery-attach step.
- [x] Battery attach (JP1 re-bridged or J2 shorted): charge current ≈100mA
      (R3 10k → 0.25C for a 400–500mAh pouch); CHG LED solid while charging.
      Charging is indoor-only, 0–45°C (no TS pin on MCP73831).
      2026-07-29 board 1 (JP1 never cut; PPK2 ampere meter in series on
      the battery + lead — charge current flows board→battery, so VIN
      faces J1): **102.97mA CC for the first ~7s — PROG confirmed.**
      Then start/stop cycling (~10↔100mA comb, aliased at 100S/s,
      envelope declining): series resistance offsets the voltage the
      charger sees, so CV/termination and recharge cycle early. Two
      co-suspects, same signature: the measurement harness (PPK2 burden
      + Dupont crimps) and the test pack's own internal resistance (a
      pouch idle for ~2 years; the other packs live in running
      prototypes). Not a charger-fault signature either way — PROG and
      the CC plateau are the checks, and they passed. Confirm with a
      known-good pack, meterless: CHG solid → terminates. Don't charge
      the aged pack unattended.

**Phase 1 complete on board 1 (2026-07-29).**

## Phase 2 — firmware smoke test (`pio run -e thermometer_c6_debug`)

First smoke build 2026-07-29: `thermometer_c6_debug`, hash `3b42d3a`, no
extra flags, `USE_BMP58x` + `DISABLE_DISPLAY` + LEDs enabled (no panel on
the board yet). Bring-up panel is the **GDEM0154I61** (`USE_154_GDEY`) —
the as-shipped JP2 0.47Ω + JP5 10µH are its correct config per the README
jumper table; the T81 stays on the soak rig for now. Flash log in
[`docs/history-store-validation.md`](../../../docs/history-store-validation.md).

- [x] Flash over USB; serial monitor up.
      2026-07-29 board 1: flashed at 3b42d3a; boot log captured via
      devserial. Full boot→sense→persist→sleep on first power: base
      snapshot seq 1 (erase 4ms / program 12ms / verify 4ms), LP core
      started at 5s poll, deep sleep entered (port drops — normal).
- [x] Boot log has **no 32k-XTAL fallback warning** → RTC slow clock is the
      FC-135 (CONFIG_RTC_CLK_SRC_EXT_CRYS). If it falls back: that's the
      32k cold-start item in Phase 3; R9 10M is the bench-stuff mitigation.
      2026-07-29 board 1: **no fallback warning — FC-135 running.**
      (W-level logs demonstrably reach this console: wifi W lines print.)
- [x] BMP581 detected at 0x47 on LP I2C (GPIO6/7); temperature plausible.
      2026-07-29 board 1: **chip ID 0x50 detected, 29.79°C** — plausible
      for a warm July room + board self-heat.
- [x] Logged battery mV ≈ DMM VBAT ±50mV (divider ×2 + curve-fitting cali);
      VDIV_EN measured 0V outside the read window.
      2026-07-29 board 1: **panel 4178mV vs 4200mV PPK2-sourced at J1 =
      −22mV — pass** (through Q6 + harness). VDIV gating proven by the
      18.7µA sleep floor rather than a pin probe: an ungated divider
      would add ~5µA. (Earlier USB-only reading of 4196mV was the
      charger's float-held node, also consistent.)
- [x] vbus_present(): true on USB, false unplugged.
      2026-07-29: false-case demonstrated behaviorally — full render
      cycles on battery-path power, no spurious shutdown. Remaining
      direct check (optional): DMM J5 pin 6 (VBUS_SENSE divider) — a
      clean DC level with USB in, 0V without.
- [x] Status LED on GPIO15 works (needs a rig whose header leaves
      `DISABLE_LEDS` undefined — see `include/rigs/`).
      2026-07-29 board 1: observed lighting on a wake.
- [x] Panel attached (power off first): full refresh renders; BUSY light-sleep
      path works; EPD_VCC returns to 0V after hibernate and the floated control
      pins don't back-light the panel rail (probe EPD_VCC). 2026-07-29 board 1,
      GDEM0154I61: **first render PASS** — 33.9°C / 16:01 CEST / 4204mV /
      `! DEBUG 5s` / footer `#3 r3 lp2 0d w:ULP mx4.2V 91bd4d8`. `w:ULP` = the
      frame came from an LP delta wake; `#3 r3` = archive continuity across the
      reflash; the refresh itself proves the boost chain
      (GDR/RESE/pump/PREVGH/PREVGL) on the as-shipped 0.47Ω/10µH. Temp read high
      then decayed toward the 27°C room — handling + USB self-heat (Phase 3
      quantifies). Still open here: EPD_VCC probe after hibernate (expect the
      floating few-hundred-mV, not 3.3V).
- [x] Deep-sleep floor on PPK2 (reference: XIAO C6 rig ~15.8µA; the LDO tree
      will differ — record the number in docs/notes.md power logbook).
      2026-07-29 board 1: **18.3µA @ 4.2V** through the J1 deployment path,
      flat across a 2397s quiet window ≈ the ~46min field interval
      (docs/notes.md 2026-07-29; the first capture's 18.6–18.8µA was the
      board still shedding USB-era heat).
- [x] LP core survives sleep cycles: lp counter increments, no echo boots,
      no `uN`/PANIC forensics indicators on screen.
      2026-07-29 board 1: `w:ULP` frames on both builds (debug 5s and
      release 60s), `lp2` alive, **no `uN`, no `! PANIC`** across the
      release capture's sleep cycles. Delta wakes rendered frames at
      exactly the LP cadence while the board cooled.

**Phase 2 complete on board 1 (2026-07-29).** The EPD_VCC probe after hibernate
stays open in [`../BRINGUP.md`](../BRINGUP.md).

## Phase 3 items closed on boards 1 and 2

- [x] **3V3 sag during the ~465mA refresh peak** — measured via the BOD probe
      (below), and the thresholds re-derived: **3550 warn / 3500mV shutdown**
      applied 2026-07-31 (Thermometer.cpp, board-scoped; the XIAO keeps
      3800/3700). Revisit hooks: a cold (~0°C) and a real-cell BOD-probe run
      decide between 3500 and 3450. [SCHEMATIC-VERIFICATION] The regime map half
      is automated: `ppk2.py sweep --rail reva-j1` (fresh boot + classification
      per 100mV step 4.2→3.0V, then a 10mV bisect of the edge — `tools/ppk2.py`
      docstring has the flow). Flash
      `PLATFORMIO_BUILD_SRC_FLAGS="-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI" pio run -e thermometer_c6_debug -t upload`
      first, detach serial, USB out; closeout = revive on USB, reflash release
      (gets the shutdown latch back), append report.md to the notes.md power
      logbook. The sweep sees input current only, so the 3V3-sag half runs as a
      **BOD probe** (no scope needed): flash `thermometer_c6_bod_probe` — the
      same image plus `sdkconfig.defaults.bod_probe`, brownout level raised to
      its ~3.27V top setting — and re-run the sweep. A refresh-peak dip below
      the trip level becomes a BROWN reset, which the classifier reads as a
      non-HEALTHY step. HEALTHY at a step proves 3V3 held above ~3.27V through
      the ~425mA peak; the topmost edge minus 3.27V ≈ LDO dropout at that peak.
      If the 4.2V step itself fails, this chip's trip point sits above its rail
      (3.3V ±1%) — drop the overlay to SEL_3 (3.10V). ROM download mode ignores
      the raised level, so USB reflash always recovers a bootlooping board.
      **Sweep DONE 2026-07-30** (notes.md): fresh-boot cliff **3317–3320mV**,
      ≤1–2mV wide; render never failed down to 3.31V, the sleep is what breaks
      (~104µA / ~55Hz oscillation below the edge); floor rises 19→30µA over
      3.38→3.32V. **BOD probe re-run on board 2 + T81, 2026-08-12** (notes.md):
      SEL_2 is unusable here — it boot-loops at 4.23V input, always at the
      render — so the run used **SEL_3 (~3.10V)**. Edge solid at 3600mV,
      **bistable at 3550**, dead at 3540, so droop ≈ **450–500mV** against board
      1's ~300mV: the T81 pulls the rail ~150–200mV deeper. **The shipped
      3550/3500mV thresholds nevertheless hold** — at the shipped brownout level
      this board and panel are HEALTHY at 3.50V with the functional cliff at
      ~3.3V, the same place board 1 found it, so the panel changes the rail
      excursion without changing where the board stops working. Cold remains the
      open gate on 3500 vs 3450. **BOD probe DONE 2026-07-30** (notes.md BOD
      subsection): the rail crosses the ~3.27V trip when VIN ≤ ~3.57V
      (stochastic 3.56–3.59, deterministic churn ≤3.55) → **total droop at the
      ~425mA peak ≈ 300mV** (LDO dropout + harness IR + trip-estimate error) —
      near the datasheet worst case, not comfortably better. At 3450mV every
      refresh peak pulls the rail to ≈3.15V on a stiff source, ~150mV over the
      C6's 3.0V spec min. Candidate thresholds **3550/3450mV** — decide after
      the cold + real-cell checks above; the droop number argues the
      conservative end (~3500–3550 shutdown). **Caveat, and why this is being
      re-run 2026-08-11: every number in this item is the 200×200 panel's.** The
      ~425mA peak, the ~300mV droop and the 3550/3500 constants derived from
      them were all taken on board 1 wearing a GDEM0154I61. The T81 is 21× the
      pixel count; its peak is bigger and has never been measured. If it droops
      further, the shipped threshold is wrong in the **unsafe** direction — it
      would let the rail cross the BOD trip on a refresh before the firmware
      ever decides to shut down. Board 2 + T81 sweep started 19:26Z
      (`local/sweeps/ppk2-sweep-20260811-192621/`), BOD probe to follow; compare
      the fresh-boot cliff and the topmost failing step against the board 1
      figures above.
- [x] **USB flash-service window** (`fc9e72c`). Plug a host into a sleeping
      board: expect a near-instant GPIO4 wake (measure plug→boot), `w:USB` in
      the footer, `! USB` on the panel, and the by-id port appearing **and
      staying**. Then `pio run -e thermometer_c6_debug -t upload` with nothing
      touched, twice back to back — the second proves the cycle converges rather
      than needing a button again. 2026-07-30 board 1: **PASS** — `! USB` on
      panel, port continuously enumerated (45s/45s vs ~1s-on/4s-off asleep),
      **two back-to-back hands-free reflashes at ~18s each**, board returning to
      the running app. Two further flashes went through the window on 2026-07-30
      and 2026-07-31. **The wake is not reliably near-instant**: the host probe
      is timing-marginal against Linux USB autosuspend, and a slow boot made the
      first probe find no SOF and log `charger, not a bus` — the window opened
      ~50s later on the re-probe. Seen again 2026-07-31.
      - [x] **Sleep floor with GPIO4 armed** vs the 18.7µA baseline. Expected
            unchanged (R23 holds the pad at 0V, and the internal pulldown is
            disabled by `CONFIG_ESP_SLEEP_GPIO_ENABLE_INTERNAL_RESISTORS=n`),
            but this measurement is the proof, not the reasoning.
            2026-07-30 (notes.md): **no measurable cost** — matched against the
            settled 18.3µA floor to 0.04µA at equal elapsed time. The capture
            never settled, so it cannot bound the cost below ~0.1µA; nothing in
            the data justifies the controlled interleave that would.
      - [x] `-DUSB_WINDOW_OBSERVE_CYCLES=2`: exactly two real sleep cycles
            (port drops each time), then the port comes back and stays. Reflash
            and confirm it repeats without touching the cable.
            2026-07-30 board 1: exactly two real deep sleeps then the window,
            logging `USB host attached, but this sleep is an observe cycle`.

Thresholds and floor/refresh numbers were done on 2026-07-31 (`1e1048e`,
`../../../docs/notes.md`).

## Deployment panel on board 2, 2026-08-11

Four GDEH0576T81 landed; one went onto board 2, which until then had run
panel-less since 2026-08-05. It worked on the factory bridges (JP2 0.47Ω +
JP5 10µH) with no rework, the third controller family to do so.
`rev A + BMP581 + GDEH0576T81` had never been measured before that day: every
earlier battery-life claim for the product substituted both a different board
and a different panel at once. Phase 3 was no longer gated on board 1 leaving its
soak; board 1 kept soaking, untouched, and every Phase 3 item could be run on
the real configuration rather than on the 200×200 stand-in. The first T81 refresh figures ever
taken at the correct waveform date from here: until 2026-08-11 the panel was
driven with its ≤5 °C LUT at room temperature (a GxEPD2 fork bug, fixed by
moving to stock upstream), so every earlier T81 number in this project,
including the readme's ~45 mC, is at the wrong LUT and does not carry over
(`../../../docs/notes.md`).

- [x] **VGH/VGL reach spec during refresh with JP2+JP5**, at the
      pre-regulation rails. **DONE 2026-08-11 at the pre-regulation rails, and
      the answer is no sag.** Measured at **PREVGH (C5) +20.031 V** and
      **PREVGL (C11) −19.380 V**, means repeating to 20 mV / 73 mV across 4-5
      refreshes, held flat for the whole ~3.03 s drive of the **LUT 235
      waveform**, the heaviest this panel can be given, and the reason the
      cold arm was used rather than a room-temperature one. Factory JP2 0.47Ω
      + JP5 10µH, nothing reworked. Full numbers and the shape (step to
      +19.885 V, climb to +20.08 V within ~300 ms, then flat) in
      `../../../docs/notes.md`. **This is what the rev B deletion of L2/R15/R16 was
      gated on**; with three controller families also working on the
      universal config, JP3+JP6 is margin nothing has needed. Two limits:
      measured *ahead of* the panel's internal regulation, so C1/C2 themselves
      are still formally unmeasured; and 10 Hz sees nothing under ~100 ms, so
      "no sag" means none on a 100 ms timescale. The C1/C2 half stays open in
      `../BRINGUP.md`.

## Soak start, 2026-08-12

Boards 2 and 4 went on the ten-day soak and board 3 was flashed to start that
evening, all on one release build (`753afbc` on 3 and 4, `11cd8dd` on board
2; the commits between are documentation only, so the firmware is identical).
Board 3 was the last board reachable on USB. The FPC-in/out floor pair
capture, the ~2 h that would explain board 2's 19.05 µA floor against board
1's 18.3 µA, was rigged and ready and was traded for the soak start; it stays
open in `../BRINGUP.md`. From then on board 2 carried the whole campaign.
