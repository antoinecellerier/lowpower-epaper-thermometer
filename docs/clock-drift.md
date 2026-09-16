# Clock drift logbook

Deep-sleep timekeeping error, measured at each NTP resync. Data rows are
append-only; add an entry per harvest and a row to the results table.

## Results

Rate = drift / window in ppm, window-weighted over the run. Positive = device
clock ahead of real time. "Spread" is the widest single deviation from the
mean, as the `! DRIFT` badge reports it.

| Rig | Slow clock | Run | Rate (ppm) | Spread | Window / n | Status |
|---|---|---|---|---|---|---|
| FireBeetle E + BMP390L + Z90 | INT_RC | badge read, 2026-07-25 | +5265 (panel read −5265, sign corrected below) | — | 21d / 1 | superseded |
| FireBeetle E | INT_RC | phase 1, 2026-07-26 .. 2026-08-04 | +5066 | ±4.5% | 10.11d / 10 | harvested 2026-08-05 |
| FireBeetle E | INT_RC | arm 1, pinned 24 repaints/day, 2026-08-05 .. 2026-08-23 | +5124.6 (+5123.2 without first record) | ±2.0% | 18.01d / 35 | harvested 2026-08-23 |
| FireBeetle E | INT_RC | arm 2, pinned 288 repaints/day, 2026-08-24 .. 2026-09-16 | +4801 | ±2.2% | 23.02d / 46 | harvested 2026-09-16, running compensated |
| XIAO C6 + BMP581 + Seeed hat I6FD | INT_RC | forced-refresh read, 2026-07-26 | +452 ±35 | — | 19.95d / 1 | not device-measured |
| XIAO C6 + Seeed hat | INT_RC | phase 1, 2026-07-27 .. 2026-08-02 | +305 | ±63% | 6.76d / 3 | harvested 2026-08-05 |
| XIAO C6 + Seeed hat | INT_RC | arm 3, vanilla, 12h resync, 2026-08-08 .. 2026-08-23 | +607 | ±96% | 14.41d / 16 | harvested 2026-08-23 |
| XIAO C6 + Seeed hat | INT_RC | arm 4, pinned 24 repaints/day, 2026-08-25 .. 2026-09-16 | +320 | ±100% | 23.02d / 42 | harvested 2026-09-16, running |
| XIAO C6 + BMP581 + DESPI-C02 + T81 | INT_RC | photo run, 2026-07-29 .. 2026-08-04 | +1259 | ±12% | 5 × 1d | photos only |
| XIAO C6 + DESPI-C02 + T81 | INT_RC | arm 5 leg 1, vanilla, 12h resync, 2026-08-05 .. 2026-08-23 | +878 | ±96% | 17.85d / 32 | harvested 2026-08-23 |
| XIAO C6 + DESPI-C02 + T81 | INT_RC | arm 5 leg 2, 2026-08-24 .. 2026-09-16 | +1322 | ±54% | 23.09d / 45 | harvested 2026-09-16, running |
| rev A board 1 + BMP581 + GDEM0154I61 | FC-135 | soak, 2026-08-01 .. 2026-08-15 | −8.5 ±1.5 (settled −6.6) | — | 15.04d / 4 | retired 2026-08-23 |
| rev A board 2 + BMP581 + T81 | FC-135 | soak, 2026-08-12 .. 2026-08-19 | −19.7 ±2.8 (settled −17.3) | — | 7.07d / 3 | retired 2026-08-23 |
| rev A board 4 + BMP581 + T81 | FC-135 | soak, 2026-08-12 .. 2026-08-19 | −6.6 ±2.8 (settled −5.8) | — | 7.06d / 3 | retired 2026-08-23 |
| rev A board 3 + BMP581 + T81 | FC-135 | soak from 2026-08-12 18:27 | unmeasured | | | on soak, unreachable |

"Settled" FC-135 rates exclude each run's first record (see the 2026-08-23
harvest). Quote the settled figures. FC-135 spread is quantization-bound (±1s
on a whole-second clock per record), so the ±ppm on the rate is the figure.

## How the number is produced

`maybe_ntp_resync()` (`src/Thermometer.cpp`) reads the clock just before a fresh
SNTP exchange and again right after:

```
last_drift_ms = (before_sync - after_sync) * 1000   // + = clock ahead, - = behind
last_resync_interval_s = resync_interval_s          // observation window
```

Surfaced four ways:

- serial: `NTP resync: drift was <n> ms over <n> s` and `NTP resync: rate <n> ppm`
- display: `! DRIFT -9559s/21d -5265ppm n4 +-3%` in the status line, only when
  |drift| ≥ 60s (`src/DisplayRenderer.cpp`): signed drift over the measured
  window, mean rate, sample count, dispersion
- display: `! NOSYNC x2 14d` while resync attempts fail (count in a row, age
  since the clock was last set)
- footer `s<N><m|h|d>`: age of the last successful sync

The on-screen ring (`RTC_DATA_ATTR`, `DRIFT_PPM_HIST_SIZE` = 6) is lost on
power-cycle, flash or panic. Every observation is also journaled as `REC_DRIFT`
to the `history` flash partition, uncapped, surviving all three:

```
~/.platformio/penv/bin/python3 tools/history.py backup
python3 tools/history.py dump local/archives/hist-*.bin --drift
```

The dump carries drift, window, ppm, mean ambient over the window, the
boot/refresh deltas and the `arm` byte. Harvest from the journal, not the badge:
the badge shows the last six samples only. Attaching USB enters download mode
and wipes the RTC drift window, so harvest at the end of a run.

### The rate summary

Windows are not uniform: the resync interval is adaptive and every failed
attempt stretches the next window by a whole interval. So:

- each sample is stored as a rate (ppm = drift / its own window);
- the mean is window-weighted: total drift / total observed time;
- `+-N%` is the widest single deviation from that mean, not a standard
  deviation and not peak-to-peak;
- samples from windows under `DRIFT_MIN_WINDOW_S` (6h) are dropped. Drift is
  read off a whole-second clock, so a sample's noise floor is ~1s per window:
  12ppm over a day, 280ppm over an hour.

A tight `+-N%` over a few stable days shows the rate is locally constant, not
that it holds across seasons.

The adaptive interval: drift `< 60s` doubles it (cap 28d); `≥ 60s` targets 60s
of drift at the next resync, clamped to `[1d, 28d]`. A cold boot starts at the 1d
floor. Builds since 2026-07-25 compute the target from the measured window
(`last_drift_window_s`), not the interval setting.

### Reading a datapoint

- Drift accumulates since the clock was last set (boot or last successful
  resync), not since the last attempt. The badge window is that measured span.
- Builds before 2026-07-25 showed the interval setting as the window. A failed
  resync re-armed `next_resync_time` without recording anything, so the true
  window was a multiple of the displayed one. Cross-check the footer uptime: a
  badge still at the 7d cold-boot default means every attempt failed and uptime
  is the window.
- The hash clips on the 200x200 panel, so the status line repeats it there.
  Resolve a prefix with `git log --pretty='%h %ad %s' | grep -E '^<prefix>'`.
  Builds before `1ad746a` (2026-05-25) measured ~0 drift and never showed the badge.
- Failed resyncs are not journaled, but each one stretches the next window by
  one interval. A window that is an integer multiple of the setting is the record
  of a failure.
- The archive header's `formatted by` hash names the build that formatted the
  store, not the one that wrote a record. Attribute records by the panel hash
  and the flash log (the C6 hat case, phase-1 entry below). `history.py`
  prints `formatted by`, flags a hash git cannot resolve, and adds
  `last snapshot written by <hash>`.

## Clock source per board

| Env | RTC slow clock | Error |
|---|---|---|
| `dfrobot_firebeetle2_esp32e_*` | `CONFIG_RTC_CLK_SRC_INT_RC` (150kHz RC) | +5066ppm measured, ±4.5% |
| `seeed_xiao_esp32c6_*` | `CONFIG_RTC_CLK_SRC_INT_RC` | +305 .. +1322ppm measured, ±50–100% |
| `thermometer_c6` (rev A) | `CONFIG_RTC_CLK_SRC_EXT_CRYS` (FC-135 32.768kHz) | −5.8 .. −17.3ppm measured (spec ~20ppm) |

Neither stock board carries a 32.768kHz crystal. The rev A board adds one.
All crystal-less rigs run fast; all three FC-135 boards run slow.

## Runs

### FireBeetle badge read, 2026-07-25

First drift badge seen on this project: −9559s over 21d, −5265ppm. Read as
+5265ppm (sign correction below).

Conditions: FireBeetle 2 ESP32-E + BMP390L + GDEH0154Z90, `95c7b04`/`95de00c`
(2026-07-03), ambient 21–32°C over the window (device's own 30-day chart).

| Quantity | Value | Source |
|---|---|---|
| drift | −9559s (−2h39m) | panel badge |
| window | 21d (badge said 7d) | footer uptime 21d |
| rate | −5265ppm (−0.53%, −7.6min/day) | drift / 21d |
| next interval | 1d (clamped) | |

The badge's 7d is the interval setting on this build. A day-7 success would
have re-armed to 1d or 14d, so the day-7 and day-14 attempts both failed and
the window is the whole uptime. The naive 7d reading, −15806ppm, is 3× too
large. The rate is a temperature-weighted average over 21–32°C.

Sign: the ten journaled samples of the 2026-08-05 harvest put this oscillator
at +4839 .. +5247ppm, and the sign convention has not changed since `346d27f`
(2026-04-05). No duty cycle this firmware can reach produces a negative rate
(the phase-1 fit needs ~7900 wakes/day, one per 11s, against a 60s interval).
The row is a transcription error off a clipped 200x200 status line. All rigs
measured here run fast.

Open: why 2 of 3 resyncs failed in this window. It did not recur (10 of 10 in
phase 1); the `! NOSYNC xN` badge catches the next episode, and the serial log
separates `WiFi failed` from `sync failed`.

### C6 ePaper hat forced-refresh read, 2026-07-26

+452ppm, +780s over 19d22h47m, from a forced refresh, not from a resync.

Conditions: XIAO ESP32-C6 + BMP581 + Seeed ePaper hat (GDEW029I6FD), `1ed89a3`
(2026-07-06), `seeed_xiao_esp32c6_epaper_release`, 400mAh pack, basement with
no WiFi, ambient 21.5–24.5°C (30-day chart). `DISABLE_SERIAL`, no `history`
partition, so the panel is the only record.

| Quantity | Value | Source |
|---|---|---|
| panel vs real | 11:54 vs 11:41 | forced refresh, both to the minute |
| drift | +780s (+13min) ±60s | |
| window | 19d22h47m | uptime 19d23h less the drift; clock set once at install |
| rate | +452ppm ±35ppm (+0.045%, ≈ +39s/day), +418 .. +487ppm | ±60s over the window |
| lower bound | ≥ +338ppm | photo 13min earlier: EXIF 11:30:17 (phone on network time, within 50s of laptop NTP) vs panel `11:40`, frame ~3min stale at the 1–2min refresh cadence it ran while carried (+3 boots, +3 refreshes in 4 LP ticks) |
| next interval | 1d floor, never left | every attempt failed; footer `s19d` |

Every resync failed for 20 days and `resync_interval_s` stayed at the 1d floor
(failures re-armed without backing off; fixed 2026-08-09, `2fccb5f`). With
WiFi, +452ppm would settle the interval near 1.5d (60s / 452ppm). This build
divides by the interval setting rather than the measured window, so its first
resync after a failure run would read the rate 20× high.

### FireBeetle phase 1, 2026-07-26 .. 2026-08-04

+5066ppm window-weighted, ±4.5%, ten daily samples, all ten resyncs succeeded.

Conditions: FireBeetle 2 ESP32-E + BMP390L + GDEH0154Z90, `44ba5ba`
(2026-07-25), `dfrobot_firebeetle2_esp32e_release` (`DISABLE_SERIAL`, 60s
interval), on battery, flash erased before the flash. Harvested 2026-08-05
10d13h in, `history.py backup --full` over the CH340 at 921600.

```
sync_time,drift_s,window_s,ppm,ambient_c,ambient_hours,boot_count,d_boot,refresh_count,d_refresh
2026-07-26 19:49:54Z,426.0,86696,4913,22.9,24,388,,297,
2026-07-27 19:50:16Z,453.0,86875,5214,24.3,24,506,118,373,76
2026-07-28 20:16:51Z,459.0,88454,5189,23.7,24,650,144,451,78
2026-07-29 20:26:11Z,447.0,87407,5114,25.5,24,757,107,506,55
2026-07-30 20:47:06Z,443.0,88098,5028,25.4,24,1033,276,724,218
2026-07-31 20:41:36Z,432.0,86502,4994,24.4,24,1318,285,924,200
2026-08-01 20:44:19Z,421.0,86984,4839,23.3,24,1650,332,1174,250
2026-08-02 20:47:48Z,434.0,87043,4986,23.9,24,1848,198,1302,128
2026-08-03 20:57:54Z,459.0,87465,5247,25.5,24,1932,84,1348,46
2026-08-04 21:11:56Z,450.0,87692,5131,26.2,24,2109,177,1465,117
```

| Quantity | Value |
|---|---|
| rate | **+5066ppm** (4424s over 873216s = 10.11d), +4839 .. +5247, ±4.5% |
| windows | 86502–88454s, all one interval: 10 of 10 resyncs succeeded |
| samples | 10 in the journal, 6 on the badge |
| next interval | 1d (clamped) |

Panel photographs before the harvest (EXIF `DateTimeOriginal`, +02:00):

| Captured | Source | Rig | Panel | Frame age | Status line | Footer | Batt |
|---|---|---|---|---|---|---|---|
| 2026-08-02 14:25:28 | `DSC_6093` | FireBeetle `44ba5ba` | 14:09 | 17–24min | `! DRIFT +421s/1d +5063ppm n6 +-4%` | `#1820 r1295 lp0 7d16h w:ULP mx4.2V 44b` | 4052mV |
| 2026-08-05 11:35:29 | `DSC_6111` | FireBeetle `44ba5ba` | 11:30 | 6–13min | `! DRIFT +450s/1d +5037ppm n6 +-4%` | `#2335 r1634 lp0 10d13h w:ULP mx4.2V 44b` | 4020mV |
| 2026-08-05 11:35:01 | `DSC_6110` | C6 + Seeed hat `431b7b0` | 11:17 | ~18min | no badge | `#1846 r1797 lp13938 9d13h w:ULP mx4.3V 431b7b0 Jul26'26 s…` | `4.32V` (stub) |

Badge cross-check: the last six samples recompute to 5063ppm ±4% at the
2026-08-02 photo and 5038ppm ±4% at 2026-08-05 (1ppm is integer truncation).
Panel transcription is exact to the digit on this rig. The panel reads behind
real time in both frames (−16.5 and −5.5min) although the clock runs fast:
that is frame staleness, which is why a photo only bounds drift.

At +5066ppm, keeping drift under 60s needs a ~3.4h interval; the 1d floor
means daily resyncs with up to ~7.3min of error before each.

Correlations, n=9 windows with deltas:

| Correlate | r | p | partial r, controlling mean ambient |
|---|---|---|---|
| wakes/day (`d_boot`) | −0.900 | 0.001 | −0.881 |
| mean ambient °C | +0.457 | 0.22 | +0.275 (controlling wakes) |

Fit: `ppm ≈ 5339 − 1.342 × wakes/day` (5226ppm at 84 wakes, 4894 at 332).
Wakes are delta-triggered, so wakes/day measures room volatility: against the
254 hourly rows, wakes/day correlates +0.926 with total variation, +0.861 with
window swing, +0.981 with mean intra-hour spread (ppm: −0.806, −0.780,
−0.867). `d_boot` and `d_refresh` correlate +0.993. A tempco in temperature
level is ruled out; duty cycle and a movement-sensitive tempco are not separable
here. Phase 2 was built to separate them and found neither (arms 1, 3, 5).

Window-mean ambient spanned only 22.9–26.2°C.

### C6 ePaper hat phase 1, 2026-07-27 .. 2026-08-02

+305ppm window-weighted, ±63%, three samples, one failed attempt.

Conditions: same board as the 2026-07-26 read, `431b7b0` (2026-07-26),
`seeed_xiao_esp32c6_epaper_release`, 400mAh pack, booted 2026-07-26 ~19:00Z,
open space at ~1.4m with windows open. Harvested 2026-08-05 (9d13h) by polling
`/dev/serial/by-id`, manual BOOT+RST park after 229s.

```
sync_time,drift_s,window_s,ppm,ambient_c,ambient_hours,boot_count,d_boot,refresh_count,d_refresh
2026-07-27 19:46:33Z,22.0,87338,251,24.4,24,88,,73,
2026-07-31 20:08:53Z,139.0,347079,400,24.7,96,821,733,787,714
2026-08-02 13:49:44Z,17.0,150068,113,23.2,41,1431,610,1395,608
```

| Quantity | Value |
|---|---|
| rate | **+305ppm** (178s over 584485s = 6.76d), +113 .. +400, ±63% |
| quantization | 11.4 / 2.9 / 6.7ppm per sample; the spread is real |
| next interval | 3.47d; next attempt due ~2026-08-06 01:00Z, after the harvest |
| interval band | 1.7–3.5d, hunting rather than pinned at the floor |
| panel 2026-08-05 | no badge (`DSC_6110`): last drift under 60s, so under 694ppm at the 1d floor; `4.32V` is the stock XIAO stub |

The adaptive interval reconstructs exactly:

| Sync | Setting | Window | Verdict | Next |
|---|---|---|---|---|
| 2026-07-27 19:46Z | 1.00d | 1.011d | on schedule | 22s < 60s: doubles to 2d |
| 2026-07-31 20:08Z | 2.00d | 4.017d | one failed attempt ~2026-07-29 19:46Z | 139s ≥ 60s: targets 1.736d |
| 2026-08-02 13:49Z | 1.74d | 1.737d (150068s vs 150000s target) | on schedule | 17s < 60s: doubles to 3.47d |

Wake-rate/ppm pairs 87→251, 182→400, 351→113 are not monotone, so the
FireBeetle's r=−0.900 does not reproduce at n=3. Window-mean ambient spans
23.2–24.7°C, narrower than the FireBeetle's 22.9–26.2°C, because 1–4 day
windows (96h at the longest) average out the volatility the placement was meant
to add. The `! NOSYNC x1` badge was up for the two days until the 07-31 success.

Archive header: `formatted by 8712f72`, orphaned. The 2026-07-26 sensor-identity
work went `57d33e4` → `5bf8129` → `8712f72` (19:29–19:32 CEST), was squashed
into `92da552` at 20:34 and landed as `431b7b0` at 21:18; the base snapshot at
17:55:34Z is 23min after `8712f72`, so the device was flashed from the
intermediate state and every drift record postdates the `431b7b0` flash.

### C6 + DESPI-C02 photo run, 2026-07-29 .. 2026-08-04

+1259ppm window-weighted, ±12%, five daily samples transcribed off photographs.

Conditions: XIAO ESP32-C6 + BMP581 + DESPI-C02 + GDEH0576T81, `44e56b6`
(2026-07-06), `seeed_xiao_esp32c6_release`, 400mAh pack, booted ~2026-07-06
22:40. The build predates the `history` partition (`8b57f33`, 2026-07-25), so
nothing can be re-read. Capture times are EXIF `DateTimeOriginal` (+02:00,
phone on network time).

| Captured (EXIF) | Source | Panel | Frame age | Drift | ppm | `#` | `r` | `lp` | Uptime | `s` | 24h range |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-07-29 12:19:56 | `DSC_5977` | 11:14 | ~67min | +115s/1d | +1331 | 1572 | 1341 | 32652 | 22d13h | 12h | 23.7–26.3°C |
| 2026-07-30 06:34:40 | `DSC_5987` | 06:34 | ~0–1min | +102s/1d | +1181 | 1640 | 1399 | 33820 | 23d8h | 7h | 24.8–27.3°C |
| 2026-07-31 13:07:48 | `DSC_6021` | 13:05 | ~4min | +96s/1d | +1111 | 1993 | 1749 | 35669 | 24d15h | 14h | 21.0–26.5°C |
| 2026-08-02 14:25:02 | `DSC_6092` | 13:59 | ~27min | +116s/1d | +1343 | 2334 | 2085 | 38638 | 26d16h | 14h | 21.5–25.1°C |
| 2026-08-04 17:04:20 | `DSC_6108` | 16:42 | ~24min | +115s/1d | +1331 | 2451 | 2188 | 41704 | 28d18h | 16h | 24.5–27.0°C |

Frame age is derived: `staleness = drift_at_render − (panel − real)`, with
drift prorated by the `s` age. All five are under the hourly safety-net refresh.
A photo bounds drift from below only; here it confirms sign and magnitude on
all five. The 2026-07-30 frame (panel 06:34 vs EXIF 06:34:40) settles that the
device is on the phone's local time, so the run is not a `MY_TZ` artefact.

The `/1d` is the interval setting, but the `s` ages (7–16h) show no attempt
failed, so it is also the window. At +1331ppm the rule targets 12.5h and clamps
to the 1d floor. `lp` advances 1450–1457/day across all four gaps (1168/19.3h,
1849/30.5h, 2969/48.9h, 3066/50.7h); boots and refreshes swing 55–278/day.
The panel's `4321mV` is the stock XIAO stub in `read_battery_level()`.

Five 24h ranges span 21–27.3°C with no monotone relation to rate (highest and
lowest rates at 23.3°C and 23.7°C mean); 5 points over ~3°C of mean ambient
cannot resolve a tempco. A constant +1259ppm correction would leave ~±150ppm ≈
13s/day at the 1d floor, against 60s allowed.

### Phase 2 design, firmware 2026-08-05

Phase 1 could not separate duty cycle from room volatility, because
delta-triggered wakes make wakes/day a measure of the room. Phase 2 pins the
wake cadence and varies only the refresh cadence.

Firmware: the delta thresholds and `DISPLAY_TEMP_DELTA` became
`#ifndef`-guarded; `REFRESH_EVERY_N_WAKES` repaints off the wake counter;
`ULP_ALWAYS_WAKE` makes the cadence timer-driven; `RESYNC_INTERVAL_MIN=43200`
pins the resync at 12h. Wakes are held at 1440/day because
`update_hourly_history()` runs only on HP wakes: at 24 wakes/day each hour would
hold one sample, `min == max == avg`, and the intra-hour-spread covariate
(+0.981 with wake count in phase 1) would vanish. Read as an awake/asleep
mixture, the phase-1 slope implies 21.7s per event against a measured ~21s Z90
refresh and a 710ms bare wake, so the refresh cadence is the term to vary. An
arm is self-identifying by `! EXP <id> <n>s` on the panel (ranked with the lab
badge) and by an `arm` byte in every drift record (`EXPERIMENT_ARM`, the
record's spare byte, no `HS_FORMAT` bump).

| Arm | Rig | Hash | Cadence | Ran |
|---|---|---|---|---|
| 1 | FireBeetle E + BMP390L + Z90 | `1ea3cd7` | pinned 1440 wakes/day, repaint every 60th (24/day) | 2026-08-05 .. 08-23 |
| 2 | FireBeetle E | `ef27bd0` | pinned 1440 wakes/day, repaint every 5th (288/day) | 2026-08-23 .. , harvested 09-16 |
| 3 | XIAO C6 + Seeed hat I6FD | `2fa3750` | vanilla, 12h resync | 2026-08-05 .. 08-23 |
| 4 | XIAO C6 + Seeed hat | `cfcc35f` | pinned 1440 wakes/day, repaint every 60th | 2026-08-23 .. , harvested 09-16 |
| 5 | XIAO C6 + DESPI-C02 + T81 | `f5e1749` | vanilla control, 12h resync, never reflashed | 2026-08-05 .. , harvested 08-23 and 09-16 |

The three 2026-08-05 hashes differ by docs-only commits
(`history-store-validation.md`). The crossover builds are HEAD of 2026-08-23,
so ~18 days of firmware change rides along with the cadence change. Crossover
happened at day 18, not the scheduled day 15.

The first record of every arm is discarded: `drift_state_load()` restores the
pre-flash `resync_interval_s` (86400s), so the first attempt runs off the old cadence
and its window straddles the regime change while carrying the new arm byte.

### Phase 2 gates

All gates passed. Day-4 values are panel reads of 2026-08-09 (uptime to the
hour, so rates are ranges); later values are from the harvests.

| Gate | Expected | Observed | Date |
|---|---|---|---|
| day-4 footers | | arm 1 `#6039 r104 lp0 4d3h w:ULP mx4.2V`, arm 3 `#563 r550 lp6092 4d4h w:ULP`, arm 5 `#718 r708 lp6100 4d3h w:ULP` | 2026-08-09 |
| arm 1 wakes/day (`#` ÷ uptime) | ≈1440 (1449–1464 with the E's fast clock, a ~1.5% surplus) | 1449–1464; 1452.9 at day 18 | 2026-08-09, 08-23 |
| arm 1 mean wake interval | 60s programmed, 59.7s real | 59.0–59.6s (arms 3, 5: 10.7min, 8.3min) | 2026-08-09 |
| arm 1 refreshes/day | 24 + 1 daily clear | 25.0–25.2; 25.05 at day 18 | 2026-08-09, 08-23 |
| arm 1 `#` ÷ `r` | 57.6 | 58.07; 58.00 at day 18 | 2026-08-09, 08-23 |
| arm 1 `! EXP 1 60s`, arm 3 `! EXP 3 60s`, arm 5 `! EXP 5 60s` | present | present | 2026-08-09 |
| arm 1 `/12h` on the drift badge | present | `! DRIFT +222s/12h +5119ppm n6 ±1%`; ring saturated, ~3 days | 2026-08-09 |
| arm 1 rate under the phase-1 duty-cycle fit | +3385ppm at ~1456 wakes/day | +5119ppm (1734ppm miss; badge span alone spans 4744–5139ppm, so take the aggregate); +1.0% from phase 1's +5066 | 2026-08-09 |
| arm 1 spread | | ±4.5% (n=10, 1d windows) → ±1% (n=6, 12h windows) | 2026-08-09 |
| arm 1 `lp` | `lp0`, structural on the FSM board | `lp0` | 2026-08-09 |
| arms 3, 5 vanilla baseline | counters track the room | 134–135 / 172–174 wakes/day, 131–132 / 170–172 refreshes/day, `#` ÷ `r` 1.02 / 1.01, LP 1448–1462 / 1464–1479 per day | 2026-08-09 |
| `e<n>` / `u<n>` tokens | absent | absent on all three (6092 + 6100 LP wakes) | 2026-08-09 |
| arm 3 resync health | `s` under 12h | `s4` clipped by the 296x128 panel; no `! NOSYNC`, no `! DRIFT` (a 4d window at +305ppm accrues ~105s, a 12h window ~13s) | 2026-08-09 |
| `d_boot` ≈ 720 per 12h window, uncorrelated with volatility | pinned | 1433–1456/day, r(wakes, spread) +0.887 via ambient only | 2026-08-23 |
| `d_refresh` ≈ 12 per window | pinned | 23.97–26.00/day | 2026-08-23 |
| hourly `min_c ≠ max_c` | 60 samples/hour | yes | 2026-08-23 |
| `arm` column 1 / 3 / 5 | not 0 | 35 at 1, 17 at 3, 32 at 5 | 2026-08-23 |
| arm 2 day 1 (~1h) | `! EXP 2 60s/RESYNC/REFRESH`, `#` ÷ `r` → 5.0 | footer `#61 r13 lp0 0d w:ULP mx4.2V ef27bd0`: floor(61/5)+1 = 13 exactly, 4.69 converging; `! DRIFT +221s/12h +5085ppm n6 ±0%` (restored ring); 4136mV; no `! NOWIFI`/`! NOSYNC` | 2026-08-23 |
| arm 4 day 1 | `lp` ≈ `#` (LP pin reached the binary) | 1:1 at harvest, 34441 vs 34442 | 2026-09-16 |
| arm 2 day 24 | 1440 wakes/day, `#` ÷ `r` 5.0 | 1454–1457, 4.99, 0 of 46 failed | 2026-09-16 |
| arm 4 day 24 | 1440 wakes/day, `#` ÷ `r` 58 | 1453–1456, 58.1, 4 of 46 failed | 2026-09-16 |

The arm 3 day-4 gate recorded `resync_fail_count == 0`; the harvest found 12
failures in 16 successes, invisible on a panel too small for the `s` token. The
first arm 4 flash silently lacked the LP pin (`.claude/rules/ulp.md`). The
200x200 footer clips after `mx4.2V` (`tools/mock_200x200_exp.png`), so arm 1's
hash is read off the status line and its sync age is not panel-readable. The
vanilla controls repaint on ~98% of wakes against ~70% in the FireBeetle's
phase-1 run; at 45mC/refresh (2026-07-03) arm 5's ~171 repaints/day is ~7.7
C/day, derived not measured.

### Arm 1 harvest, 2026-08-23

+5124.6ppm window-weighted, ±2.0%, n=35. Phase 1's duty-cycle fit predicted
+3385ppm at this arm's wake rate; the miss is 1740ppm.

Conditions: FireBeetle E + BMP390L + Z90, `1ea3cd7`, pinned 1440 wakes/day and
24 repaints/day, 12h resync, on battery. Panel before the cable: `! EXP 1 60s`,
`! DRIFT +221s/12h +5085ppm n6 ±0%`, 4029mV, footer
`#26274 r453 lp0 18d2h w:ULP mx4.2V`. Image
`local/archives/hist-arm1-firebeetle-20260823.bin`: 691 hourly, 320 sparkline,
45 drift, 2026-07-25 19:00Z .. 2026-08-23 13:00Z, `formatted by 44ba5ba`,
`last snapshot written by 1ea3cd7`.

| Quantity | Value |
|---|---|
| rate | **+5124.6ppm**, +7975s over 18.01d (35 × 12h), +5041 .. +5229, ±2.0% |
| without the first record | +5123.2ppm, n=34, residual sd 46.5ppm (0.9% of the rate; pre-registered guess ±51ppm) |
| first record | 24.0h window against a 12h setting, `d_boot = −658` (RTC wipe) |
| phase-1 subset (`arm`=0, 10 records) | +5066.3ppm over 10.11d, +4840 .. +5248, ±4.5%: matches the published +5066 |
| drift per sample | +219s .. +445s |
| pack | 4029mV at day 18 |

The archive round-trips a published figure across a reflash. The rate moved
+1.1% from phase 1 across a 7× increase in wakes/day (4.4× the busiest phase-1
day), so the duty-cycle model is dead; the spread tightened ±4.5% → ±2.0%,
which fits the phase-1 slope having fitted estimator noise that tracked wake
count.

Residual correlations, n=34 (5% critical |r| ≈ 0.34):

| Covariate | Range | raw r | partial r |
|---|---|---|---|
| intra-hour spread | 0.03 .. 0.81°C | −0.443 | −0.045 (controlling ambient) |
| mean ambient | 21.4 .. 29.7°C | +0.476 | +0.200 (controlling spread) |
| wakes/day | 1433.3 .. 1456.2 (±0.8%) | −0.476 | −0.005 (controlling ambient) |
| refreshes/day | 23.97 .. 26.00 | +0.081 | |
| elapsed days | 0 .. 16.4 | −0.079 | |

The volatility hypothesis is refuted: its signal collapses once ambient is
held. Ambient's own partial is not significant. Ambient and wakes/day
correlate at −0.999: with the cadence timer-driven, `d_boot` reads the slow
clock's tempco directly, and the RC slows when warm (fewer 60s sleeps per
window). The drift rate rises when warm (+0.476), the opposite sign. Ambient
explains 23% of the residual variance, so the drift leg is the weak one.

Open: the sign disagreement between the wake counter and the drift rate. Arm 2
(12× the repaints, same wake cadence) tests whether the awake path carries the
opposite tempco.

### Arm 3 harvest, 2026-08-23

+607.2ppm window-weighted, ±96%, n=16, with 12 failed attempts (43%).

Conditions: XIAO C6 + BMP581 + Seeed hat I6FD, `2fa3750`, vanilla, 12h resync,
400mAh pack. Panel before the park: `! EXP 3 60s`, footer
`#1808 r1621 lp26405 18d3h w:ULP mx4.3V 2fa3750`. Image
`local/archives/hist-arm3-xiao-hat-20260823.bin`: 667 hourly, 320 sparkline, 20
drift, 2026-07-26 19:00Z .. 2026-08-23 13:00Z, `formatted by 8712f72`
(orphaned), `last snapshot written by 2fa3750`.

| Quantity | Value |
|---|---|
| rate | **+607.2ppm** over 14.41d, +23 .. +1184, ±96%, +1s .. +158s per sample |
| failures | 12 in 16 successes; windows of 24h, 36h, 37h, 49h against a 12h setting |
| first record | 3.49d window against 12h (restored 3.47d interval, archive not erased), `d_boot = −893`, dropped |
| phase-1 subset (`arm`=0, 3 records) | +304.5ppm over 6.76d, ±63%: matches the published +305 |
| wakes/day | 135.1 at day 4, 99.8 lifetime, 89.2 over days 4–18 |
| refreshes/day | 132.0 / 89.4 / 76.7; `#` ÷ `r` 1.024 → 1.115; lp/day 1462.1 → 1456.8 |

The level doubled from phase 1's +305 (n=3) but neither figure is tight enough
to call that a change. The room quietened by a third over the run, confirmed by
arm 5 over the same days (174 → 75 wakes/day there).

| Covariate | arm 3 (n=16) | arm 1 (n=34) |
|---|---|---|
| raw r(ppm, ambient) | +0.577 | +0.476 |
| raw r(ppm, spread) | −0.558 | −0.443 |
| raw r(ppm, wakes/day) | −0.550 | −0.476 |
| partial r(ppm, spread \| ambient) | −0.229 | −0.045 |
| partial r(ppm, ambient \| spread) | +0.287 | +0.200 |
| partial r(ppm, wakes \| ambient) | −0.290 | −0.005 |

Same raw signature and same collapse on two oscillators 8× apart in rate; the
5% critical |r| is ~0.51 at n=16. Arm 5 shows neither correlation. No
mechanistic covariate survives on any arm.

### Arm 5 harvest, 2026-08-23

+877.9ppm window-weighted, ±96%, n=32. No covariate correlates except elapsed
time.

Conditions: XIAO C6 + BMP581 + DESPI-C02 + T81, `f5e1749`, vanilla, 12h resync,
400mAh pack, ran untouched 2026-08-05 .. 08-23. Panel before the park:
`! EXP 5 60s`, footer
`#1763 r1596 lp26499 18d2h w:ULP mx4.3V f5e1749 Aug5'26 s6h`, 23.5°C. Image
`local/archives/hist-arm5-xiao-t81-20260823.bin`: 32 drift, 17.85d observed, 435
hourly, `arm` = 5 throughout.

| Quantity | Value |
|---|---|
| rate | **+877.9ppm** ±3.7ppm quantization, +1354s over 17.85d, +324 .. +1721ppm (±96%), +14s .. +112s per sample |
| per-sample quantization | ±11 .. 23ppm; the scatter is 15–70× the rounding |
| failures | 3 windows carry a failed attempt |
| wakes/day | 97.5 lifetime, 174 at day 4, 74.9 over days 4–18; refresh/wake 0.986 → 0.905 |

| Covariate | Range | r vs ppm |
|---|---|---|
| wakes/day | 31 .. 364 | +0.026 |
| refreshes/day | 4 .. 364 | +0.013 |
| mean ambient | 20.7 .. 30.1°C | −0.058 |
| intra-hour spread | 0.00 .. 0.95°C | +0.044 |
| window length | 0.50 .. 1.04d | +0.110 |
| elapsed time | 0 .. 17.85d | +0.487 (Spearman +0.401; +0.498 / +0.400 without the failed-attempt windows) |

Phase 1's `r=−0.900` duty-cycle relation is absent over a 12× range of wakes at
n=32 (phase 1: ten samples over 84–332 wakes/day). Elapsed time clears the 1%
line (|r| 0.449 at n=32): slope +28.7ppm/day, first half +742ppm, second half
+1005ppm. Ambient was not monotone (25.6 → 30 → 23°C). Supply voltage is
journaled nowhere and the stock XIAO cannot read its pack
(`include/HistoryStore.h` has no battery field), so pack drain and sleep die
temperature stay unseparated. Adding mV to the drift record needs an `HS_FORMAT`
bump.

For compensation: the 2026-07-25 rules put ±M% > ~10% at "futile", and a
constant fitted on this run's first half is ~260ppm wrong by its second.

### FC-135 soak, rev A boards 2, 3 and 4: t=0 record, 2026-08-11/12

Three rev A boards on the FC-135 crystal, sealed on battery; no USB until
harvest. Conditions: GDEH0576T81, BMP581, 400mAh pack, `thermometer_c6_release`,
rig `revA-bigscreen`, no flags, `esptool erase_flash` immediately before flashing.

| Board | MAC | Hash | Started | Pack at t=0 | Placement |
|---|---|---|---|---|---|
| 4 | `10:bd:a3:a8:d3:64` | `753afbc` | archive created 2026-08-11 22:24:26Z, first window ~22:29Z | 3996mV at `#2 r2 lp1 w:ULP` | paired with 2, ~10cm |
| 2 | `98:88:e0:75:48:10` | `11cd8dd` | 2026-08-11 22:49Z (first window ~22:47Z) | 3998mV (second render; first read 4004mV) | paired with 4 |
| 3 | `98:88:e0:75:47:94` | `52cf257`, different `MY_WIFI_NETWORKS` | 2026-08-12 18:27 local, NTP-synced at first boot | 4188mV (4186mV at the fourth render) | another location, different AP |

The three hashes are one firmware: `git diff 753afbc..11cd8dd` and
`753afbc..52cf257` over
`src include ulp components platformio.ini sdkconfig.defaults*` are empty. Board
3's binary differs only through the gitignored `include/local-secrets.h` network
list. Boards 2 and 4 hold static DHCP leases; board 3 holds a dynamic lease on
its AP, a resync term that is not journaled (`HistoryDriftSample` has no connect
duration; `resync_fail_count` and the absolute counters are journaled).

The pair started ~20 minutes apart; the "2026-08-12" in earlier notes is local
time. Packs: boards 2 and 4 run as ordered, never charged (an as-shipped cell
near 4.00V is roughly three-quarters charged, LiPo-curve estimate); board 3 was
charged to full, hence ~190mV higher (~4.19V). Every pack read ~4000mV on its own board before
charging, which bounds per-board divider spread at tens of mV. The 6mV step
between board 2's first two renders is unexplained (not surface charge; the
pack was never charged). Cutoffs are `low_battery_mv = 3550` /
`no_battery_mv = 3500`, so board 3 has 688mV of span against the pair's
~497mV. Compare discharge as rates over a common window, never as days to a
voltage. At harvest both pair packs took ≲5mAh of USB charge (~1% of the cell).

Design: 2 vs 4 (same room, same firmware, same windows) isolates part-to-part
spread; 3 vs the pair isolates the room; 2 and 4 also run two BMP581s in the
same air. Board 2 carries the fleet's bench history (BOD probe, 3.0V sweep).
Each board sleeps at ~90µW, so mutual heating is not a confound.

### FC-135 harvest, 2026-08-23

All three measured FC-135 boards run slow, inside the ~20ppm spec: −8.5, −19.7
and −6.6ppm window-weighted (settled −6.6, −17.3, −5.8).

Conditions: boards 2 and 4 read at day 11.6 (soak 2026-08-12 .. 08-19 for
windows), board 1 at day 23.0 (soak 2026-08-01 .. 08-15 for windows;
`711c3a4` of 2026-07-31, rig `revA-smallscreen`, GDEM0154I61, another room,
never through the BOD campaign). Board 3 unreachable. Panels photographed
before any cable. Images `local/archives/hist-revA-board{2,4}-20260823.bin`,
full partition. Board 1's firmware predates the `last snapshot written by`
field.

| | board 2 | board 4 | board 1 |
|---|---|---|---|
| footer | `#498 r347 lp16737 11d14h w:ULP mx4.0V 11cd8dd Aug12'26 s4d` | `#504 r341 lp16747 11d15h w:ULP mx4.0V 753afbc Aug12'26 s4d` | |
| pack | 3998 → 3964mV, −2.93mV/day | 3996 → 3962mV, −2.92mV/day | 4086mV at day 23; start unlogged (~4200mV assumed), ~−4.9mV/day bounded, on a steeper part of the curve than the pair's −2.9mV/day |
| ambient at read | 23.0°C | 22.9°C | |
| wakes/day, refreshes/day | 43.0, 30.0 | 43.4, 29.3 | 60.6 |
| lp/day | 1444.9 | 1440.6 | 1442.3 (0.3% agreement across the three) |
| badges | none | none | |

Drift records (±quantization is ±1s over the window):

| Record | board 2 | board 4 | board 1 (wakes/day, ambient) |
|---|---|---|---|
| 1 | 1.03d, −3s, −33.6ppm ±11.2 | 1.04d, −1s, −11.2ppm ±11.2 | 1.00d, −3s, −34.7ppm ±11.6 (104.9, 25.3°C) |
| 2 | 2.01d, −5s, −28.9ppm ±5.8 | 2.02d, 0s, 0.0ppm ±5.8 | 2.01d, −1s, −5.8ppm ±5.8 (65.2, 25.3°C) |
| 3 | 4.03d, −4s, −11.5ppm ±2.9 | 4.00d, −3s, −8.7ppm ±2.9 | 4.03d, −2s, −5.7ppm ±2.9 (74.0, 26.0°C) |
| 4 | | | 8.01d, −5s, −7.2ppm ±1.4ppm, the tightest single sample taken (48.7, 26.3°C) |
| window-weighted | −19.7ppm ±2.8 (−12s / 7.07d; widest deviation ±71%, quantization) | −6.6ppm ±2.8 (−4s / 7.06d) | **−8.5ppm** ±1.5 (−11s / 15.04d) |
| settled (first record dropped) | −17.3ppm / 6.03d | −5.8ppm / 6.02d | −6.6ppm / 14.04d |
| next interval | 8d | 8d | 16d |

| Pair | Gap | σ |
|---|---|---|
| board 1 − board 4 | −1.9 ± 3.2ppm | 0.6 |
| board 1 − board 2 | +11.2 ± 3.2ppm | 3.5 |
| board 2 − board 4 | −13.1 ± 4.0ppm | 3.3 |

Boards 1 and 4 agree (0.8ppm apart on settled rates); board 2 is the outlier.
The mean of the three is −11.6ppm, all negative. A 13ppm spread is ordinary for
a ~20ppm-tolerance crystal, and board 2's rate is stable across its windows, so
damage is neither required nor excluded. Board 2's |ppm| falls with wake rate
(77 → 30 → 29/day); board 4 on the same windows shows no trend, so the slope is
noise. In every run the first window is both the shortest and the busiest (105,
77, 77 wakes/day against 30–74 later), which confounds window length with wake
rate by construction. No `! DRIFT` on any board: at ~20ppm the 60s badge needs
~50 days. `s4d` is the doubling interval (successes ~d1, d3, d7). Board 1's
discharge is not comparable to the pair's: different start voltage, 200x200
panel against 920x680, 60.6 against 43 wakes/day.

Open:
- board 3, unmeasured;
- the first-record bias and the shared slow sign (next entry).

### FC-135 first-record bias and load-cap hypothesis, 2026-08-23

Each board's first (1d) record is more negative than its settled rate predicts,
and all three settled rates share a negative sign.

| Board | 1d record | Settled rate predicts | Excess |
|---|---|---|---|
| 1 | −3s | −0.57s | −2.43s |
| 2 | −3s | −1.54s | −1.46s |
| 4 | −1s | −0.52s | −0.48s |

Same sign on 3 of 3; board 1's excess is beyond the ±1s a whole-second clock
explains. The restored-interval mechanism of the phase-2 arms does not apply
(all three erased before flash). Board 1's first window opens 2026-07-31
13:08:07Z, 18min after its ~12:50Z pack-in, so no unpowered gap sits inside it.
Candidates: a cold-path first SNTP exchange, bench handling on day 1.

Shared sign: rev A fits 2×20pF for a CL=12.5pF FC-135
(`hardware/thermometer-c6/SCHEMATIC-VERIFICATION.md`); two 20pF in series
present 10pF, so CL lands on 12.5pF only if stray is ~2.5pF. At ~5pF stray the
crystal sees CL≈15pF and is pulled slow:

    Δf/f = (C1/2) × [1/(C0+CL_nom) − 1/(C0+CL_act)]
         = (2.5fF/2) × [1/13.7pF − 1/16.2pF] ≈ 14ppm slow

with typical tuning-fork values (C1≈2.5fF, C0≈1.2pF), not the FC-135
datasheet's. Order of magnitude only.

Open:
- the first-record bias mechanism;
- the load-cap test: add a few pF across one crystal leg on a retired board and
  re-measure (rev B candidate in `hardware/thermometer-c6/BRINGUP.md`).

### BMP581 part-to-part in situ, boards 2 vs 4, 2026-08-11 .. 2026-08-23

Two BMP581s in the same air agree to within storage resolution.

Conditions: rev A boards 2 and 4, ~10cm apart, hourly rows from the soak
journals, mean ambient 26.9°C over 20.3–30.1°C.

| Quantity | Value |
|---|---|
| overlapping hourly rows | 279, 2026-08-11 22:00Z .. 2026-08-23 12:00Z |
| board 2 − board 4, hourly average | mean +0.003°C, median 0.000, sd 0.055°C |
| within ±0.1°C | 278 of 279 hours |
| histogram | 13.3% at −0.1, 70.6% at 0.0, 15.8% at +0.1, one hour at +0.2 |
| storage resolution | 0.1°C (`int16` ×10), so agreement is bounded at ≤0.1°C |
| mean intra-hour spread | 0.08°C on both boards |

### Arm 2 harvest, 2026-09-16

+4801ppm window-weighted, ±2.2%, sd 42.5ppm, n=46. Predicted ≈ +4790 before
the read from an awake/asleep mixture.

Conditions: FireBeetle E + BMP390L + Z90, `ef27bd0`, pinned 1440 wakes/day and
288 repaints/day, 12h resync, on battery, 2026-08-24 .. 09-16. Panel before the
cable: `! EXP 2 60s/RESYNC/REFRESH`, `! DRIFT +210s/12h +4799ppm n6 ±1%`,
3688mV, footer `#34541 r6918 lp0 23d17h`. Image
`local/archives/hist-arm2-firebeetle-20260916.bin`, 47 records at `arm`=2, all
12h, 0 failed; the first (`d_boot = −25286`) dropped.

| Quantity | Value |
|---|---|
| rate | **+4801.2ppm**, +9548s over 23.02d, +4696 .. +4882 (±2.2%), sd 42.5, +205s .. +210s per sample |
| pack | 4136mV at crossover (charged over USB at the flash) → 3688mV, −18.9mV/day two-point at 288 Z90 repaints/day (arm 1: −4.9mV/day at 25/day) |

| | arm 1 | arm 2 |
|---|---|---|
| rate | +5123.2 | +4801.2 |
| awake fraction (0.71s wake, 21s refresh) | ~1.8% | ~8.2% |
| sd | 46.4 | 42.5 |
| ppm per °C ambient | +8.8 | +10.3 |
| wakes/day per °C | −2.82 | −2.89 |
| partial r(ambient \| spread) | +0.200 | +0.272 |

Awake time is XTAL-clocked and sleep runs on the RC; scaling arm 1's +5123 by
the awake fractions gives +4788. Solving the two arms as a mixture: sleep path
≈ +5213ppm, awake path ≈ +195ppm (fractions derived, so approximate; the sign
is not). The ambient slope did not move and the wake-counter thermometer reads
the same, so the awake path is not the source of arm 1's sign disagreement.
Volatility partial +0.020. Elapsed time +0.2ppm/day, both halves +4801.

### Arm 4 harvest, 2026-09-16

+320ppm window-weighted, ±100%, sd 156ppm, n=42. Pinning did not tighten the
C6's relative scatter.

Conditions: XIAO C6 + BMP581 + Seeed hat I6FD, `cfcc35f`, pinned 1440 wakes/day
and 24 repaints/day, 12h resync, 400mAh pack, 2026-08-25 .. 09-16. Panel before
the park: `! EXP 4 60s/RESYNC/REFRESH`, footer `#34442 r593 lp34441 23d16h`.
Image `local/archives/hist-arm4-xiao-hat-20260916.bin`, 43 records at `arm`=4;
the first (`d_boot = −1022`) dropped; 4 of 46 attempts failed, all within the
first 5 windows.

| | arm 3 (vanilla) | arm 4 (pinned) |
|---|---|---|
| rate | +607 | **+320** (+637s over 23.02d, 0 .. +485, +0s .. +21s per sample) |
| sd | 319 | 156 |
| sd / rate | 52% | 49% |
| widest deviation | ±96% | ±100% |
| r(ppm, ambient) | +0.577 | −0.016 |
| r(ppm, wakes/day) | −0.550 | +0.008 |
| r(ppm, elapsed) | +0.192 | −0.020 |

The per-record noise floor is ~23ppm, so the 156ppm scatter is real. The level
on this board is not stable between runs: +305 (phase 1), +607 (arm 3), +320
(arm 4), with nothing journaled that separates them. The wake counter reads
ambient at −2.33 wakes/day per °C (r=−0.990; E: −2.8) while the drift rate
shows −2.4ppm/°C at r=−0.016.

### Arm 5 second leg, 2026-09-16

+1322ppm window-weighted, ±54%, sd 293ppm, n=45, no failed resync. The August
climb (+28.7ppm/day) flattened to +2.3ppm/day.

Conditions: XIAO C6 + BMP581 + DESPI-C02 + T81, `f5e1749`, vanilla, 12h resync,
400mAh pack, 2026-08-24 .. 09-16 (RST, not reflashed, at the 08-23 read). Panel
before the park: `! EXP 5 60s`, footer `#2187 r1936 lp34688 23d18h … s4h`, 92
wakes and 81 repaints a day. Image
`local/archives/hist-arm5-xiao-t81-20260916.bin`, 78 records at `arm`=5 over
41.5d; the record straddling the RST (`d_boot = −1659`) dropped.

| Quantity | Value |
|---|---|
| second leg | **+1322ppm**, +2638s over 23.09d, +647 .. +2029, +28s .. +88s per sample |
| halves | +1286 / +1356 |
| all 78 records vs elapsed | r=+0.604, from the step between legs |
| covariates, second leg | wakes +0.138, ambient +0.058, elapsed +0.053, intra-hour spread +0.299 raw / +0.295 partial (5% line at n=45, absent on every other arm) |

| Quarter of the 42 days | mean ppm |
|---|---|
| 1 | +733 |
| 2 | +1163 |
| 3 | +1302 |
| 4 | +1327 |

The RST and USB attach of 2026-08-23 sit on the leg boundary, so a reset effect
cannot be separated from a real step in the rate.

## Compensation

Decision 2026-07-25: no compensation code until several daily samples exist.
Built 2026-09-16 (`DRIFT_COMPENSATION`, FireBeetle rig only) once phase 2 had
shown the E's rate stable at ±2% with no covariate to model. The C6 rigs stay
uncorrected: their rate wanders ±50–100% with no correlate.

### What it buys

A constant-ppm correction leaves a residual equal to the rate's instability.
At R = 5265ppm = 455s/day (the 2026-07-25 figure):

| Rate stability | Residual | Error @1d | @7d | @28d |
|---|---|---|---|---|
| ±1% | 4.5 s/day | 5 s | 32 s | 2.1 min |
| ±2% | 9 s/day | 9 s | 64 s | 4.2 min |
| ±5% | 23 s/day | 23 s | 2.7 min | 10.6 min |
| ±10% | 46 s/day | 46 s | 5.3 min | 21 min |
| none | 455 s/day | 7.6 min | 53 min | 3.5 h |

Staying under 60s needs ±13% at daily sync, ±1.9% weekly, ±0.47% at the 28d
cap. Below ~±10% stability the 1d floor makes compensation worthless.

With phase 1's +5066 ±4.5%:

| Model | Residual | Interval | Attempts/year |
|---|---|---|---|
| none | ±5066ppm = 438 s/day | 1d floor, 7.3 min of error | 365 |
| constant +5066ppm | ±227ppm = ±19.6 s/day | ~3d | ~120 |
| + per-wake term (in-sample, 2 parameters on 9 points) | ±87ppm = ±7.5 s/day | ~8d | ~46 |

The payoff is WiFi wakes, not display accuracy. Floor 19.4µA = 1.68 C/day;
refreshes ~5.4 C/day at the measured ~2/hour (1077 over 21d17h = 49.6/day; 860
over 18d17h = 46.0/day). A failed attempt burns 15s (association timeout) or 45s
(SNTP timeout), 1.5–4.5 C, against a ~7.1 C/day budget. A successful WiFi+NTP
wake was unmeasured in 2026-07 (20.6mC active phase plus radio time was the
construction). Measured since: 117mC on the XIAO ePaper rig, superseded by 248mC
static lease / 321mC hotspot on rev A board 2, 2026-08-11 (`docs/notes.md`).
This cost also sets the first-sync policy in `maybe_ntp_resync()`: retrying a
never-set clock on every hourly wake would cost 36–108 C/day, so the bootstrap
retries hard within one session and then backs off to ~1 attempt/day. The
RTC-rendezvous design in [multi-device-research.md](multi-device-research.md)
(master wakes 200ms early, listens 500ms) needs ≤ ±1% residual (0.16s after an
hour).

### Decision rules (2026-07-25) and outcome

| Rule | Outcome |
|---|---|
| `+-M%` ≤ ~2%, uncorrelated with both correlates → constant-rate model, interval out to 7–28d | E pinned: ±2.0–2.2%, no correlate. Built as a constant with a recency-weighted refit. |
| tracks daily temperature → `R(T) = R0 + k(T−Tref)` over the hourly history | ambient never significant on any arm |
| tracks the boot-count delta → duty-cycle model, per-wake term | killed by arms 1, 5 and board 4 |
| `+-M%` > ~10% → futile at the 1d floor | C6 rigs: ±50–100%. Not compensated. |

### What ESP-IDF provides

IDF has no frequency compensation.

| Lever | Verdict |
|---|---|
| `CONFIG_RTC_CLK_SRC_INT_8MD256` (ESP32 only): 8.5MHz ÷ 256 (~33kHz), better stability, +5µA deep sleep (`esp_hw_support/port/esp32/Kconfig.rtc`) | untried; +5µA on 19.4µA = +0.43 C/day; check `ULP_WAKEUP_PERIOD_US` survives the change; not on the C6 |
| `CONFIG_RTC_CLK_CAL_CYCLES` (1024, up to 32766) | better boot calibration; does not fix an awake/asleep offset |
| `SNTP_SYNC_MODE_SMOOTH` / `adjtime()` (`esp_libc/src/time.c`) | rejected: slews an offset not a frequency, only under 35min of error, state is plain `static` and dies in deep sleep |
| `CONFIG_RTC_CLK_SRC_EXT_CRYS` | needs a crystal the WROOM-32E and XIAO lack; the rev A board has one |

### Mechanism

`esp_clk_init()` → `select_rtc_slow_clk()` recalibrates the RC against the 40MHz
crystal on every boot including deep-sleep wakes; `sleep_modes.c` recalibrates
at sleep entry; `esp_rtc_get_time_us()` converts ticks with the current
calibration. So a persistent error means the RC runs at a different frequency
asleep than awake being calibrated. Solving Phase 2's two E arms as a mixture
gives sleep path ≈ +5213ppm, awake path ≈ +195ppm; the awake fractions are
derived, not measured, so the split is approximate and the sign is not. Biasing
the sleep duration cannot correct wall clock: it is `boot_time + ticks × cal`
regardless of what the timer was programmed to.

### Implementation (2026-09-16, `src/Thermometer.cpp`)

| Step | Where | What |
|---|---|---|
| apply | every HP wake, right after `boot_count++` | `settimeofday()` steps the clock back by `elapsed × ppm / (1e6 + ppm)` since the last anchor |
| anchor | every clock set: boot sync, bootstrap, resync | correction measures from here |
| refit | after each successful resync | level = recency-weighted mean of the raw-rate ring, weight = window × `DRIFT_COMP_DECAY`^age (0.75 per sample) |
| arm | `DRIFT_COMP_MIN_SAMPLES` (2) windows ≥ 6h | below that, or outside ±20000ppm, nothing is applied |
| persist | `HistoryDriftState.drift_comp_ppm` | a reflash resumes from the archived level |

Once armed the resync measures the residual. The ring and the journal's `ppm`
keep the raw rate (residual + applied); the journal's `drift_ms` keeps the
residual, so `history.py dump --drift` recovers the applied level as
`comp_ppm` and `driftstats.py` reports both. `! DRIFT` fires on the residual;
the footer shows `c<ppm>` while armed; the adaptive interval climbs on the
residual. `esp_clk_slowclk_cal_set()` is unusable: `sleep_modes.c` overwrites
it at sleep entry. On the ESP32-E only 60 bytes separate the app's RTC sections
from `ULP_DATA_BASE` (`scripts/post_build_check_rtc.py`), so per-sample
covariate arrays do not fit.

Expected on the FireBeetle from arms 1 and 2: residual sd ~42ppm (3.6 s/day),
widest ~100ppm (8.6 s/day), interval settling between 7 and 16 days; the level
shifts with the awake fraction (+5123 at 25 repaints/day, +4801 at 288), which
the refit absorbs. Unmeasured until the first compensated harvest.

## Open questions

- Rate stability: answered. E ±2% pinned, ±4.5% vanilla; C6 ±50–100% on every
  run, level unstable between runs (+305 / +607 / +320 on one board).
- What the rate tracks: no per-window covariate on any arm. Duty cycle killed
  three ways (arm 1 level miss, arm 5 null over 31–364 wakes/day, board 4
  control). Volatility collapses under ambient; ambient never reaches
  significance. Arm 5 leg 1 tracked elapsed time, leg 2 did not.
- The E's wake counter says the RC slows when warm (r=−0.999 with ambient) while
  its drift rate rises when warm (+0.476, not significant). Arm 2 cleared the
  awake path. Open.
- C6 pack voltage and sleep die temperature are not journaled; adding mV to the
  drift record costs an `HS_FORMAT` bump.
- FC-135: first-record negative bias on 3 of 3 boards; the shared slow offset
  (load-cap bench test pending); board 3 unmeasured.
- Window-mean ambient spanned 22.9–26.2°C on the FC-135 run and 20.7–30.1°C on
  arm 5, against a 21–32°C instantaneous swing; a tempco outside those bands is
  untested.
- Compensation residual on the FireBeetle: unmeasured until its first harvest.
