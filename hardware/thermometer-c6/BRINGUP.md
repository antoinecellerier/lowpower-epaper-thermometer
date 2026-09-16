# BRINGUP.md — rev A bench queue

Open measurements on the rev A boards, and where each board is. The first
article (Phases 0–2 on board 1, the X-rays and every Phase 3 item closed
since) is
[`archive/bringup-rev-a-first-article.md`](archive/bringup-rev-a-first-article.md).
Measured figures live in the logbooks; an item links the entry it depends on.
Items tagged [REVIEW-KICAD-HAPPY ○], [SCHEMATIC-VERIFICATION] and [README] came
from the open rows of `REVIEW-KICAD-HAPPY.md`, `SCHEMATIC-VERIFICATION.md`, the
README bench procedures and the placement verification in
[`archive/order-2026-07-20/jlc-production-files/`](archive/order-2026-07-20/jlc-production-files/).
A new board runs Phases 0–2 in order (the archive record is the checklist);
Phase 3 measurements are taken once; the remaining boards of a batch get a
quick Phase 0–1 pass.

Bench ground rules (README): **never back-feed TP4 (3V3)**. RT9080 forbids
VOUT > VIN + 0.3V and EN=0 active-discharges at ~80Ω; inject bench power only
at the J2/JP1 battery-side break.

Test points (back side): VBAT, VBAT_ADC, 3V3 (probe-only), EPD_VCC, PREVGH,
PREVGL, VCOM, GDR, RESE, GND ×2. J2 (the `IBAT` header) spans the JP1 break:
pin 1 = battery side (VBAT_RAW), pin 2 = system side (VBAT, the charger output
node, *not* VSYS). VSYS has no TP or header; probe D2's cathode (band/west)
pad, Q1's source, or C1/C2.

## Boards, as of 2026-08-23

| Board | Panel | State | Since |
|---|---|---|---|
| 1 | GDEM0154I61 | off soak, harvested and retired, pack out; holds the only copy of its soak data outside `local/archives/` | 2026-08-23 |
| 2 | GDEH0576T81 (fitted 2026-08-11) | off soak, bench scratch: erase it freely, its soak archive is backed up | 2026-08-23 |
| 3 | GDEH0576T81 | on soak at another location, not reachable | 2026-08-12 |
| 4 | GDEH0576T81 | off soak, harvested and retired, pack out; holds the only copy of its soak data outside `local/archives/` | 2026-08-23 |
| 5 | none | bare, unassembled; factory 0005 datamatrix | 2026-07-29 |

Boards 3 and 4 carry the T81 per the FC-135 soak conditions in
[clock-drift.md](../../docs/clock-drift.md#fc-135-soak-rev-a-boards-2-3-and-4-t0-record-2026-08-1112).
Soak firmware: `753afbc` on boards 3 and 4, `11cd8dd` on board 2; the commits
between are documentation only, so the firmware is identical. Boards 2–4
never got the Phase 0 dead-short pass, deliberately; reinstate it for any
board that is reworked or that arrives from a different fab run.

## Phase 3 — first-article measurements, open items (PPK2 + scope)

Scope items still need a scope. The 10 Hz multimeter reaches the *sustained*
rails (VGH/VGL through a multi-second refresh) but not the millisecond
transients.

- [ ] **VGH/VGL at C1/C2 during refresh with JP2+JP5** (0.47Ω/10µH universal
      config). GDEH0576T81's datasheet config is 2.2Ω/47µH = JP3+JP6, the
      on-board fallback if VGH sags. The pre-regulation rails PREVGH/PREVGL
      showed no sag on 2026-08-11 (archive record;
      [notes.md](../../docs/notes.md#boost-rails-under-the-worst-case-waveform-board-2--t81-2026-08-11)),
      but that was measured *ahead of* the panel's internal regulation, so
      C1/C2 themselves are still formally unmeasured, and 10 Hz sees nothing
      under ~100 ms. Partly reachable without a scope: VGH/VGL land on
      **C2/C1** (4.7µF/25V to GND, README pin table) as SMD pads, and are held
      for the duration of a driving phase, so 10 Hz logging gets tens of
      samples across a T81 refresh. The comparisons that need no external
      reference (the firmware sends no PWR `0x01`, so these are module OTP
      defaults and nothing publishes them): VGH at PON vs mid-drive on the
      same refresh, and T81 vs a 200×200 panel on the same board and bridges.
      Measure *after* the LUT question is settled; a colder waveform loads the
      charge pump differently. [REVIEW-KICAD-HAPPY ○]
- [ ] EPD_VCC ramp with the R24/C28 soft-start on a scope (no brownout at
      gate-on). [README PPK2 items]
- [ ] EPD_VCC probe after hibernate on the panel-attached board: expect the
      floating few-hundred-mV, not 3.3V. Left open at the 2026-07-29 first
      render.
- [ ] Boost transient current vs the Si1308EDL 610mA ILIM at refresh start.
      [SCHEMATIC-VERIFICATION]
- [ ] **Cold (~0°C) and real-cell BOD-probe runs**, which decide between 3500
      and 3450 mV shutdown. The shipped 3550 warn / 3500mV thresholds hold on
      board 2 + T81 (2026-08-12, archive record); the ~300mV droop measured on
      board 1 argues the conservative end (~3500–3550 shutdown).
      [SCHEMATIC-VERIFICATION]
- [ ] 32k crystal **cold start**: power-on from fridge-cold (ESR rises when
      cold; FC-135's 70kΩ spec sits at Espressif's max). Mitigations in
      order: R9 10M bench-stuff, 7pF FC-135 variant. [REVIEW-KICAD-HAPPY ○]
- [ ] **Warm sleep floor** (~40°C): D2 SS14 reverse leakage lands on the
      floor via the 66k VBUS pulldowns; PMEG6010-class is the fallback (no
      SMA drop-in, so a board change for rev B if needed).
      [REVIEW-KICAD-HAPPY ○]
- [ ] **FPC-in/out floor pair**, the ~2 h capture that would explain why
      board 2's floor reads 19.05 µA against board 1's 18.3 µA
      ([notes.md](../../docs/notes.md#board-1-vs-board-2-floor-gap-2026-08-11)).
      Neither figure has a concurrent ambient reading, so the 4% gap is not
      yet established as a board-to-board difference rather than a thermal
      one. Rigged and ready on 2026-08-12, traded for the soak start.
- [ ] **VBAT_ADC accuracy across 3.5–4.2V vs DMM**; confirm the 5ms divider
      settle is ample (τ = 0.5ms). Protocol (2026-07-29): PPK2 source at J1,
      USB OUT (the charger fights the source for VBAT); the panel only shows
      fresh mV on a rendered frame, so press RST per step to force one.
      4.2→3.8V in 100mV steps, then below deliberately: ≤3.8V exercises the
      low-battery behavior and ≤3.7V the shutdown path (first hardware test
      of the threshold logic; revive on USB). Single points so far, both read
      on a rendered frame through the same Dupont-into-JST harness, so any
      harness IR drop at the ~15mA read current is common to both: board 1
      **−22mV at 4.2V** (2026-07-29), board 2 **−24mV at 4.2V** (2026-08-11,
      panel 4176mV under a 4200mV PPK2 source at J1, taken during the SEL_3
      BOD sweep). 2mV apart, an order of magnitude inside the ±40mV worst
      case of the per-board 1% divider stack, so the shared curve fit
      transfers and boards 3–4 are unlikely to need individual calibration;
      boards 2–4 get a single-point check (~4.0V) during their sweep.
      While looking at this trace, also check whether the settle wait shows
      as a visible chunk of a non-refresh wake. Analysis 2026-07-22 (deferred
      pending these numbers): the read runs only on CPU wakes, so the
      blocking 5ms costs ~0.075mC (5ms × ~15mA) against a multi-mC wake,
      <1%, an 8× smaller target than the already-declined 40ms EPD-reset
      light-sleep. If it ever matters, the known fixes are (a) hoist the
      VDIV_EN enable to setup() entry with an elapsed-time remainder guard in
      read_battery_level() (logging hides the settle only in debug builds),
      or (b) trim 5ms→3ms (6τ, ~10mV battery-scale error) for a
      zero-complexity 60% cut.
- [ ] **Self-heat, separated by source.** There is no usable number yet:
      board 1's 33.9°C against 29.8°C an hour earlier mixes bench sun, USB
      self-heat and the operator's fingers on the board (it decayed
      afterwards), so it bounds nothing. Take **equilibrium** deltas against
      a reference thermometer, one mode at a time, lid off and hands off:
      (a) battery only, sleeping: expect no measurable rise (calculated
          single-digit mW average);
      (b) USB parked in the service window, no pack: isolates U1+U2, the
          ~150mW continuous case;
      (c) USB with a pack charging: adds U4's ~130mW, which is 37mm away and
          so should present as whole-board warming rather than a local
          gradient. If (c) ≫ (b), the charger dominates and no sensor
          placement fixes it (README rev B candidate); if (b) ≈ (c), the
          local sources do.
      Then decide whether readings taken while charging should be suppressed
      or flagged rather than filed into the hourly ring. Cheap A/B for the
      U1-proximity term without a respin: build one of boards 2–4 with U6
      BMP585 instead of U5 and repeat (b).
- [ ] **Load-cap bench test** before any respin, now cheap. The three FC-135
      rates measured 2026-08-23 are all negative, which a symmetric initial
      tolerance would not produce; the rev A load-cap fit and the
      order-of-magnitude argument for the shared sign are in
      [clock-drift.md](../../docs/clock-drift.md#fc-135-first-record-bias-and-load-cap-hypothesis-2026-08-23).
      Add a few pF across one crystal leg on a retired board and re-measure
      the rate. Load-capacitance pulling predicts the rate moves further
      negative on a slope the formula gives; nothing else on the board
      answers that stimulus that way. A drift measurement needs days per
      point, so plan it as a soak rather than a bench afternoon, or drive it
      from a counter on the 32k pin.
- [ ] If confirmed, **trim the load caps** in rev B to re-centre the fleet.
      Files alongside the existing D2 and 7 pF-crystal-variant candidates, as
      does any part swap the items above produce.
- [ ] **USB flash-service window** follow-ups (`fc9e72c`; the 2026-07-30
      board 1 pass and the armed-GPIO4 floor are in the archive record):
      - [ ] Dumb 5V charger (no host): no rewake loop (the GPIO wake is armed
            only on VBUS-low), and the ~3s host probe appears on the PPK2 once
            per USB_WINDOW_PROBE_SKIP_WAKES wakes, not on every one. Note the
            docked cadence is deliberately the sleep interval, not the 1h
            safety net, so a docked board wakes far more often than a deployed
            one; that is what keeps the port reachable.
      - [ ] Unplug mid-window: exit inside ~300ms, one badge-clearing refresh,
            then deep sleep; replug wakes instantly again.
      - [ ] Force a refresh while the window is open: the port must survive it
            (plain busy-wait instead of light sleep). Confirm a later
            battery refresh still shows the light-sleep slices.
      - [ ] ≥2h parked on a host: hourly ring keeps filling, NTP resyncs on
            schedule, no TWDT. Watch for one benign extra wake on the first
            real sleep after a long window (a latched LP wake request); log it
            either way.
- [ ] The three deferred **WiFi PPK2 captures**
      ([notes.md open items](../../docs/notes.md#open-items)).

## What a board off soak unblocks

Boards 1, 2 and 4 came off soak on 2026-08-23. The fleet had been unavailable
for bench work since 2026-08-12, when board 3 was the last board reachable on
USB; anything marked open above waited for a board to come off, not for time.

| Item | Needs |
|---|---|
| FPC-in/out floor pair | a board off battery, ~2 h on the PPK2 |
| load-cap bench test | a retired board, days per point |
| VBAT_ADC across 3.5–4.2V | PPK2 source at J1 with USB OUT, so a board off battery |
| crystal cold start, warm sleep floor | a board that can go in the fridge or a warm box |
| WiFi PPK2 captures | a board on the PPK2 |

Two soak results worth carrying into rev B thinking: the two BMP581s on
boards 2 and 4 agreed closely over 279 hours in the same air
([clock-drift.md](../../docs/clock-drift.md#bmp581-part-to-part-in-situ-boards-2-vs-4-2026-08-11--2026-08-23))
and their packs discharged alike
([notes.md](../../docs/notes.md#rev-a-discharge-on-battery-read-at-harvest-2026-08-23)).
Part-to-part spread on this board is small everywhere it has been measured
except the crystal.
