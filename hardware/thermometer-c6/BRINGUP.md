# BRINGUP.md — rev A first-article checklist

Consolidates the bring-up items from README (Bench procedures, open items),
REVIEW-KICAD-HAPPY.md (○ OPEN rows), SCHEMATIC-VERIFICATION.md (first-article
adds), and the placement verification in
[`archive/order-2026-07-20/jlc-production-files/`](archive/order-2026-07-20/jlc-production-files/).
Run Phases 0–2 in order on the first board; Phase 3 measurements once; then a
quick Phase 0–1 pass on the remaining boards. Bench ground rules (README): **never back-feed TP4 (3V3)** —
RT9080 forbids VOUT > VIN + 0.3V and EN=0 active-discharges at ~80Ω; inject
bench power only at the J2/JP1 battery-side break.

Test points (back side): VBAT, VBAT_ADC, 3V3 (probe-only), EPD_VCC, PREVGH,
PREVGL, VCOM, GDR, RESE, GND ×2. J2 (the `IBAT` header) spans the JP1
break: pin 1 = battery side (VBAT_RAW), pin 2 = system side (VBAT — the
charger output node, *not* VSYS). VSYS has no TP or header — probe D2's
cathode (band/west) pad, Q1's source, or C1/C2.

## Phases 0–2 and the X-rays

Closed: every item closed on board 1 on 2026-07-29. The record, with the
pointer to the X-ray findings and the Phase 3 items closed since, is
[`archive/bringup-rev-a-first-article.md`](archive/bringup-rev-a-first-article.md).

## Phase 3 — first-article measurements (one board, PPK2 + scope)

**2026-08-11: the deployment panel arrived and Phase 3 is no longer gated on
board 1 leaving its soak.** Four GDEH0576T81 landed; one went onto board 2,
which until then had run panel-less since 2026-08-05. It worked on the factory
bridges (JP2 0.47Ω + JP5 10µH) with no rework — the third controller family to
do so. **`rev A + BMP581 + GDEH0576T81` had never been measured before today**:
every battery-life claim for the product substituted both a different board and
a different panel at once. What that unblocks, and the one thing it does not:

- Every item below can now be run on the real configuration rather than on the
  200×200 stand-in. Board 1 keeps soaking, untouched.
- The **first T81 refresh figures ever taken at the correct waveform**. Until
  2026-08-11 the panel was driven with its ≤5 °C LUT at room temperature (a
  GxEPD2 fork bug, fixed by moving to stock upstream). Every earlier T81 number
  in this project, including the readme's ~45 mC, is at the wrong LUT and does
  not carry over — see `../../docs/notes.md`.
- **Not** unblocked: the scope items. A 10 Hz multimeter is available, which
  reaches the *sustained* rails (VGH/VGL through a multi-second refresh) but not
  the millisecond transients.

**2026-08-12: bench access is closing — boards 2 and 4 are on the ten-day soak,
board 3 is flashed and starts this evening**, all on one release build
(`753afbc` on 3 and 4, `11cd8dd` on board 2; the commits between are
documentation only, so the firmware is identical). **Board 3 is the last board
reachable on USB** — anything below that needs a cable and not a PPK2 has until
this evening. After that, board 2 carried the whole campaign and anything still
marked open waits for a board to come off, not merely for time. What that costs,
concretely: the
**FPC-in/out floor pair** — the ~2 h capture that would explain why board 2's
floor reads 19.05 µA against board 1's 18.3 µA — was rigged and ready and was
traded for the soak start. The gap is open, and neither figure has a concurrent
ambient reading, so it is not yet even established as a board-to-board
difference rather than a thermal one. Everything needing a scope, a fridge or a
reference thermometer is in the same queue.

- [ ] **VGH/VGL reach spec during refresh with JP2+JP5** (0.47Ω/10µH
      universal config). GDEH0576T81's datasheet config is 2.2Ω/47µH =
      JP3+JP6 — that's the on-board fallback if VGH sags.
      [REVIEW-KICAD-HAPPY ○]
      Partly reachable without a scope: VGH/VGL land on **C2/C1** (4.7µF/25V to
      GND, README pin table) as SMD pads, and are held for the duration of a
      driving phase, so 10 Hz logging gets tens of samples across a T81 refresh.
      The comparisons that need no external reference (the firmware sends no PWR
      `0x01`, so these are module OTP defaults and nothing publishes them): VGH
      at PON vs mid-drive on the same refresh, and T81 vs a 200×200 panel on the
      same board and bridges. Measure *after* the LUT question is settled — a
      colder waveform loads the charge pump differently.
      **DONE 2026-08-11 at the pre-regulation rails, and the answer is no sag.**
      Measured at **PREVGH (C5) +20.031 V** and **PREVGL (C11) −19.380 V**, means
      repeating to 20 mV / 73 mV across 4-5 refreshes, held flat for the whole
      ~3.03 s drive of the **LUT 235 waveform** — the heaviest this panel can be
      given, and the reason the cold arm was used rather than a room-temperature
      one. Factory JP2 0.47Ω + JP5 10µH, nothing reworked. Full numbers and the
      shape (step to +19.885 V, climb to +20.08 V within ~300 ms, then flat) in
      `docs/notes.md`. **This is what the rev B deletion of L2/R15/R16 was
      gated on**; with three controller families also working on the universal
      config, JP3+JP6 is margin nothing has needed. Two limits: measured *ahead
      of* the panel's internal regulation, so C1/C2 themselves are still
      formally unmeasured; and 10 Hz sees nothing under ~100 ms, so "no sag"
      means none on a 100 ms timescale.
- [ ] EPD_VCC ramp with the R24/C28 soft-start on a scope (no brownout at
      gate-on). [README PPK2 items]
- [ ] EPD_VCC probe after hibernate on the panel-attached board (expect the
      floating few-hundred-mV, not 3.3V). Left open at the 2026-07-29 first
      render.
- [ ] Boost transient current vs the Si1308EDL 610mA ILIM at refresh start.
      [SCHEMATIC-VERIFICATION]
- [ ] 32k crystal **cold start**: power-on from fridge-cold (ESR rises when
      cold; FC-135's 70kΩ spec sits at Espressif's max). Mitigations in
      order: R9 10M bench-stuff, 7pF FC-135 variant. [REVIEW-KICAD-HAPPY ○]
- [ ] **Warm sleep floor** (~40°C): D2 SS14 reverse leakage lands on the
      floor via the 66k VBUS pulldowns; PMEG6010-class is the fallback (no
      SMA drop-in — board change for rev B if needed). [REVIEW-KICAD-HAPPY ○]
- [ ] VBAT_ADC accuracy across 3.5–4.2V vs DMM; confirm the 5ms divider
      settle is ample (τ = 0.5ms). Protocol (2026-07-29): PPK2 source at
      J1, USB OUT (the charger fights the source for VBAT); the panel
      only shows fresh mV on a rendered frame, so press RST per step to
      force one. 4.2→3.8V in 100mV steps, then below deliberately —
      ≤3.8V exercises the low-battery behavior and ≤3.7V the shutdown
      path (first hardware test of the threshold logic; revive on USB).
      First datapoint 2026-07-29: −22mV at 4.2V. Boards 2–4 get a
      single-point check (~4.0V) during their sweep — the curve fit is
      shared but the 1% divider stack is per-board (±40mV worst case).
      **Board 2 done 2026-08-11: −24mV at 4.2V** — panel read 4176mV under
      a 4200mV PPK2 source at J1, taken during the SEL_3 BOD sweep, no
      extra rig time. 2mV from board 1, i.e. an order of magnitude inside
      the ±40mV worst case, so the shared curve fit transfers and boards
      3–4 are unlikely to need individual calibration. Both figures are
      read on a rendered frame through the same Dupont-into-JST harness,
      so any harness IR drop at the ~15mA read current is common to both.
      The across-3.5–4.2V half of this item is still open. While looking at this trace, also check
      whether the settle wait shows as a visible chunk of a non-refresh
      wake. Analysis 2026-07-22 (deferred pending these numbers): the read
      runs only on CPU wakes, so the blocking 5ms costs ~0.075mC (5ms ×
      ~15mA) against a multi-mC wake — <1%, an 8× smaller target than the
      already-declined 40ms EPD-reset light-sleep. If it ever matters, the
      known fixes are (a) hoist the VDIV_EN enable to setup() entry with an
      elapsed-time remainder guard in read_battery_level() (logging hides
      the settle only in debug builds), or (b) trim 5ms→3ms (6τ, ~10mV
      battery-scale error) for a zero-complexity 60% cut.
- [ ] **Self-heat, separated by source.** There is no usable number yet: board
      1's 33.9°C against 29.8°C an hour earlier mixes bench sun, USB self-heat
      and the operator's fingers on the board (it decayed afterwards), so it
      bounds nothing. Take **equilibrium** deltas against a reference
      thermometer, one mode at a time, lid off and hands off:
      (a) battery only, sleeping — expect no measurable rise (calculated
          single-digit mW average);
      (b) USB parked in the service window, no pack — isolates U1+U2, the
          ~150mW continuous case;
      (c) USB with a pack charging — adds U4's ~130mW, which is 37mm away and
          so should present as whole-board warming rather than a local
          gradient. If (c) ≫ (b), the charger dominates and no sensor
          placement fixes it (README rev B candidate); if (b) ≈ (c), the local
          sources do.
      Then decide whether readings taken while charging should be suppressed or
      flagged rather than filed into the hourly ring.
      Cheap A/B for the U1-proximity term without a respin: build one of boards
      2–4 with U6 BMP585 instead of U5 and repeat (b).
- [ ] **USB flash-service window** follow-ups (`fc9e72c`; the 2026-07-30 board 1
      pass and the armed-GPIO4 floor are in the archive record):
      - [ ] Dumb 5V charger (no host): no rewake loop (the GPIO wake is armed
            only on VBUS-low), and the ~3s host probe appears on the PPK2 once
            per USB_WINDOW_PROBE_SKIP_WAKES wakes, not on every one. Note the
            docked cadence is deliberately the sleep interval, not the 1h
            safety net, so a docked board wakes far more often than a deployed
            one — that is what keeps the port reachable.
      - [ ] Unplug mid-window: exit inside ~300ms, one badge-clearing refresh,
            then deep sleep; replug wakes instantly again.
      - [ ] Force a refresh while the window is open: the port must survive it
            (plain busy-wait instead of light sleep). Confirm a later
            battery refresh still shows the light-sleep slices.
      - [ ] ≥2h parked on a host: hourly ring keeps filling, NTP resyncs on
            schedule, no TWDT. Watch for one benign extra wake on the first
            real sleep after a long window (a latched LP wake request); log it
            either way.

Thresholds and floor/refresh numbers are done (`1e1048e`, 2026-07-31; notes.md).
Still owed afterwards: file any part swaps (D2, crystal variant) as rev B
candidates, and run the cold + real-cell BOD probes that decide whether shutdown
may drop from 3500 to 3450 mV.

## Rev B candidate: the 32k load caps are the fleet's shared slow offset (2026-08-23)

The first FC-135 rates are measured (`docs/clock-drift.md`): boards 1, 2 and 4
read **−8.5, −19.7 and −6.6 ppm** over 15.0, 7.1 and 7.1 days of observed window.
All three are inside the part's ~20 ppm tolerance in magnitude, and the 13 ppm
spread between them is ordinary part-to-part scatter — but **all three are
negative**, which a symmetric initial tolerance would not produce.

Rev A fits **2×20 pF against a CL=12.5 pF FC-135** (`SCHEMATIC-VERIFICATION.md`),
i.e. two 20 pF caps present 10 pF and the design reaches 12.5 pF only if stray is
really ~2.5 pF. At ~5 pF of stray the crystal sees CL≈15 pF and is pulled slow by
roughly 14 ppm, using typical tuning-fork motional values (C1≈2.5 fF, C0≈1.2 pF)
rather than the FC-135 datasheet's — **an order-of-magnitude argument for the
shared sign, not a measurement of these boards**.

- [ ] **Bench test before any respin, now cheap**: boards 1, 2 and 4 are off soak.
      Add a few pF across one crystal leg on a retired board and re-measure the
      rate. Load-capacitance pulling predicts the rate moves further negative on
      a slope the formula gives; nothing else on the board answers that stimulus
      that way. A drift measurement needs days per point, so plan it as a soak
      rather than a bench afternoon, or drive it from a counter on the 32k pin.
- [ ] If confirmed, **trim the load caps** in rev B to re-centre the fleet.
      Files alongside the existing D2 and 7 pF-crystal-variant candidates.

## Boards 1, 2 and 4 are off soak (2026-08-23)

Harvested and retired, packs out, archives kept. Board 3 stays out on soak at
another location and is not reachable. The fleet has been unavailable for bench
work since 2026-08-12; these three unblock it:

- the **FPC-in/out floor pair** — the unexplained 4% gap, 19.05µA board 2 against
  18.3µA board 1, deferred 2026-08-12 for want of a board
- the **load-cap bench test** for the shared −11.6ppm crystal offset (above)
- **VBAT_ADC across 3.5–4.2V**, the open half of that item — the protocol wants a
  PPK2 source at J1 with USB OUT, so it needs a board off battery
- **crystal cold start** and the **warm sleep floor**, both needing a board that
  can go in the fridge or a warm box
- the three deferred **WiFi PPK2 captures** (`docs/notes.md`)

Board 2 keeps its bench-scratch status: erase it freely now that its soak archive
is backed up. Boards 1 and 4 hold the only copy of their soak data outside
`local/archives/`.

Two results from the soak worth carrying into rev B thinking: the two BMP581s on
boards 2 and 4 agreed to **+0.003°C mean over 279 hours** in the same air, and
their packs discharged within 0.4% of each other — part-to-part spread on this
board is small everywhere it has been measured except the crystal.
