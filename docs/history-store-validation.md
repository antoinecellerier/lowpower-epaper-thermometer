# Flash history archive — hardware validation log

What `src/HistoryStore.cpp` has been shown to do on hardware, and every flash,
erase, inject and backup that touched a board. Append; never rewrite a data row.
Host-only checks live in `tools/hstest` and are not repeated here.

Default rig unless a row says otherwise: FireBeetle 2 ESP32-E + BMP390L +
GDEH0154Z90, `dfrobot_firebeetle2_esp32e_debug`, `/dev/ttyUSB0`, USB-powered.

Rows before 2026-08-05 name `local-secrets.h` contents, because panel and sensor
were hand-edited there per flash. Since then the env carries its rig
(`custom_rig`, `include/rigs/`) and a rig/env mismatch is a compile error. Bench
procedure, port naming and parked-chip recovery: the `/device-session` skill.

Network names are redacted (CLAUDE.md): `<house-ap>`, `<hotspot>`, even inside
quoted serial logs.

## Rigs and identities

| Rig | Board | Panel / sensor | MAC (efuse) | Archive header MAC | Port |
|---|---|---|---|---|---|
| `firebeetle` | FireBeetle 2 ESP32-E | GDEH0154Z90 / BMP390L | `c4:5b:be:8c:4d:b8` | same | `/dev/ttyUSB0`, CH340 (`1a86` by-id) |
| `xiao-hat` | XIAO ESP32-C6 + Seeed ePaper board | GDEW029I6FD / BMP58x | `58:E6:C5:16:1F:08` | `58:e6:c5:ff:fe:16` | USB-Serial-JTAG, by-id `…16:1F:08` |
| `xiao-bigscreen` | XIAO ESP32-C6 + DESPI-C02 | GDEH0576T81 / BMP58x | `58:e6:c5:13:9b:e4` | `58:e6:c5:ff:fe:13` | USB-Serial-JTAG, by-id `…13:9B:E4` |
| rev A board 1 | thermometer-c6 | GDEM0154I61 / BMP581 | `98:88:E0:75:47:9C` | `98:88:e0:ff:fe:75` | by-id `…47:9C` |
| rev A board 2 | thermometer-c6 | GDEH0576T81 / BMP581 | `98:88:e0:75:48:10` | `98:88:e0:ff:fe:75` | by-id `…48:10` |
| rev A board 3 | thermometer-c6 | GDEH0576T81 / BMP581 | `98:88:e0:75:47:94` | `98:88:e0:ff:fe:75` | by-id `…47:94` |
| rev A board 4 | thermometer-c6 | GDEH0576T81 / BMP581 | `10:bd:a3:a8:d3:64` | | by-id `…D3:64` |

The header stores the EUI-64 form (`esp_efuse_mac_get_default()` expansion), so
boards 1, 2 and 3 share `fffe75` and `history.py`'s auto-generated backup
filename does not tell them apart. Name every image explicitly and take identity
from the dump header. Board 3 differs from board 1 in the last MAC byte only.

## Plan and status

Device-side steps from the implementation plan. Host-side equivalents pass in
`make -C tools/hstest`.

| # | Experiment | Why it needs hardware | Status |
|---|---|---|---|
| 1 | First boot on the new partition table | one-time format over the old app image | PASS 2026-07-25; format timing unmeasured (see erase note under Flash cost) |
| 2 | Archive accumulates | real ULP wakes, real refresh cadence | PASS 2026-07-25 (sparkline, then hourly at 15:00Z) |
| 3 | `history.py backup` + `dump --csv` | real esptool over the UART bridge | PASS 2026-07-25 |
| 4 | Reflash test: history survives `pio run -t upload` | the whole point | PASS 2026-07-25; round-tripped published ppm figures 2026-08-23 |
| 5 | Power-cycle test: RTC gone, restore + `HOURLY_NO_DATA` gap | | PASS 2026-07-25 (72-row gap fill via injected outage) |
| 6 | Cold-clock test: unsynced device records nothing, `NOSYNC`, bounded retries | | records nothing: 2026-07-30 (`DISABLE_WIFI` sweeps); bounded retries: 2026-08-09 |
| 7 | Transport test: baud decisive on this board | | PARTIAL: 921600 works for short reads, fails a `--full` read on the CH340 (2026-08-23); 460800 works |
| 8 | `erase_flash`: clean start, no boot loop | | PASS, many times; boot loop found and fixed 2026-07-25 |
| 9 | PPK2: append / base / erase costs vs estimates | | DONE 2026-07-25, below |

## Flash cost of a base snapshot, 2026-07-25 (ESP32-E, PPK2)

A base snapshot costs 7.14 mC, 0.1% of this rig's day. Full setup in
[`notes.md`](notes.md).

| Quantity | Value | Source |
|---|---|---|
| Base snapshot | **170.2 ms at 41.94 mA = 7.14 mC** at 3300 mV | PPK2, marker-bounded |
| Share of ~7.1 C/day at one snapshot/day | 0.1% (hourly cadence would be 2.4%) | arithmetic |
| Estimate before measuring | 5.6 mC, 27% low: current right (40 vs 41.94 mA), duration wrong | on-device timing covered only the flash calls |

On-device timing of the flash calls alone:

| Phase | Time | Note |
|---|---|---|
| erase 2 sectors (8 KB) | 104-125 ms | ~53 ms/sector, set by the flash part |
| program 6.4 KB payload | 25 ms | one page-aligned write; three calls (header, RtcHistory, drift) cost 66 ms |
| read back + CRC32 | 7-8 ms | |
| marker overhead | ~13 ms | CRC32 over payload + malloc/memcpy |

Batching the payload into one page-aligned write took 21% off the snapshot. The
pre-measurement estimate for the program phase was 13 ms, 5x off. Erase-rate
extrapolation put the one-time format of 480 sectors at ~26 s (the code's ~24 s
guess); a full-chip 4 MB `erase_flash` then took 1.7 s (2026-07-26) and 1.2-1.5
s later, so the format is likely erase-block bound (30 aligned 64 KB blocks) and
single-digit seconds. Open: the format itself has never been timed.

### Recovery point objective

The hourly archive's RPO is one hour, from the journal alone. `journal_append()`
writes each hourly entry as its hour finalizes, so a reflash, panic or battery
pull loses at most the hour in progress. The base snapshot covers the rest:

| Data | RPO | Journal-backed? |
|---|---|---|
| Hourly archive | **~1 h** | yes |
| Drift samples | ~1 day (one per resync) | yes, `REC_DRIFT` |
| `resync_interval_s`, `resync_fail_count` | 24 h | no; both re-derive after one sync |
| 24 h sparkline | 24 h | no, base only |
| Restore anchor | 24 h | no; `history_store_restore()` bails without a valid base |

`HS_BASE_MAX_RECORDS = 24` pins the snapshot cadence at about a day. Before that
the only non-NTP trigger was a full journal sector (256 records, 10.7 days), so
the cadence was the adaptive resync interval: 1 day on the FireBeetle only
because its −5265 ppm drift pins the interval at its floor, up to the 28-day cap
on a crystal board. Owning the cadence raised the cost from ~0.7 to 7.1 mC/day.
A finer sparkline cadence was not taken: the sparkline refills within a day.

## Clean-state recipe (first used 2026-07-25 16:55Z, FireBeetle)

```
esptool erase_flash
pio run -e dfrobot_firebeetle2_esp32e_debug -t upload
```

Verified on 2026-07-25 at `99390e1`, clean tree, no `PPK2_DEBUG`, no
`HISTORY_BASE_EVERY_WAKE`: archive `0 hourly, 1 sparkline, 0 drift`, base seq 1
at cursor 0x000000, drift block at defaults (`resync_interval_s 86400`,
`ppm_hist` zero, `drift_ppm_count 0`, `last_sync_time` from a real sync).
Anything injected by `hstest --inject` must be erased before a measurement run,
or the fabricated drift sample joins the ring and the first real measurement is
computed against an invented `last_sync_time`.

## When the archive stops recording

The store degrades instead of panicking. The device keeps measuring, charting and
refreshing while every hour is lost; `! NOARCH` is the only signal that reaches
the panel, since `DISABLE_SERIAL` removes the log line from release builds.

| Badge | Meaning | What to do |
|---|---|---|
| `! NOARCH fmt<N>` | on-flash format N, firmware speaks another | `history.py backup --full`, then `esptool erase_flash` and reflash |
| `! NOARCH nopart` | no `history` partition, device on an old table | reflash; the upload rewrites the partition table |
| `! NOARCH io` | an erase or write failed | suspect the flash part; back up if it still reads |

Rendered by `tools/sim` as `mock_*_noarch.png`. Ranked ahead of the crash badge:
a crash's payload is already in the coredump partition, this condition is still
destroying data. `! NOARCH fmt2` has never been photographed on a panel; serial
line and simulator render are verified (2026-07-25).

## Header timestamp

`store created` is stamped in `store_format()`, in `setup()` before the first
NTP sync, and the header sector is never rewritten. On a fresh device it is
epoch zero, printed by `history.py` as "(before first NTP sync)". With a battery
holding the RTC through `erase_flash` the fresh format inherits the old wall
clock instead (board 1, 2026-07-31; board 4, 2026-08-11). Not worth a format
change. The header's `formatted by` hash is the build that formatted the store,
not the build that wrote any record; attribute data by the panel hash and this
log. Example: the hat's header says `built 8712f72`, a commit on no branch: the
2026-07-26 sensor-identity work was `57d33e4` → `5bf8129` → `8712f72` (19:29-19:32
CEST), flashed from that state, then squashed into `92da552` at 20:34 and amended
four times into `431b7b0`. Expect `formatted by` to become unresolvable after a
squash.

## Device state

Every flash, erase and inject. Flags are `PLATFORMIO_BUILD_FLAGS` through
2026-08-05 and `PLATFORMIO_BUILD_SRC_FLAGS` from 2026-08-09 (every macro is read
under `src/`, and `scripts/check_ulp_size.py` preprocesses with `build_src_flags`).
"none" means a production-identical build. Sizes are `firmware.bin` bytes where noted.

| Date | Board / rig | Env | Flags | Hash | Erase | Note |
|---|---|---|---|---|---|---|
| 2026-07-25 | FireBeetle | `dfrobot_firebeetle2_esp32e_debug` | none | `b10cd29` (from `95c7b04-dirty`) | no | relocation to the new table; first format |
| 2026-07-25 | FireBeetle | same | none | `f050bfc` | no | anchor / outage-fill test (`1f6552d`), injected 30-day archive |
| 2026-07-25 | FireBeetle | same | none | `HS_FORMAT` 2→3 test build (`19dde9f`) | no | archive left intact and disabled, byte-identical |
| 2026-07-25 16:55Z | FireBeetle | same | none | `99390e1` | yes | clean state for the drift collection; see also `44ba5ba` below |
| 2026-07-25 | FireBeetle | same | none | `44ba5ba` | | the build the 2026-08-05 harvest found running "from the 2026-07-25 clean flash"; the flash itself has no row |
| 2026-07-26 | `xiao-hat`, PPK2 4.2 V at shield JST | `seeed_xiao_esp32c6_epaper_release` | `-DPPK2_DEBUG` | `4c0bbef` | no | first archive on this board; relocation from `factory` 0x10000 (`1ed89a3`, 19d23h basement run) to 0x1f0000; written `--before no_reset --after no_reset` |
| 2026-07-26 | `xiao-hat` | same | `-DPPK2_DEBUG` | `4c0bbef` | yes (1.7 s) | re-armed the first-boot capture after the board booted on USB by mistake |
| 2026-07-26 | `xiao-hat` | same | `-DPPK2_DEBUG` | `f07d2c9` | no | archive from the previous boot kept |
| 2026-07-26 | `xiao-hat` | same | none | `91f08eb` | no | production build to test whether the sleep-floor hump exists without `PPK2_DEBUG` |
| 2026-07-26 | `xiao-hat` | same | `-DPPK2_DEBUG` | `e8fb31e` (1000402 B; 1000114 B without the flag) | no | 80 ms marker fingerprint every wake; analyse with `--decimate 1` |
| 2026-07-26 | `xiao-hat` | same | none | `2d90340` (1000114 B) | yes (1.5 s) | clean state after a spurious 127.5 °C reached flash |
| 2026-07-26 | `xiao-hat` | same | none | `-dirty` (early plausibility gate) | no | sensor-fault test |
| 2026-07-26 | `xiao-hat` | `seeed_xiao_esp32c6_epaper_debug` | none | (session builds) | no | fault rendering and recovery tests |
| 2026-07-26 | `xiao-hat` | `seeed_xiao_esp32c6_epaper_release` | none | `431b7b0` (1008016 B) | no | production build with the sensor-identity work; archive found empty, one base snapshot from 17:55:34Z before the first sync |
| 2026-07-29 | rev A board 1, USB, no panel | `thermometer_c6_debug` | none | `3b42d3a` | factory blank | `USE_BMP58x` + `DISABLE_DISPLAY`, LEDs on; first power |
| 2026-07-29 | board 1 + GDEM0154I61 | same | none | `91bd4d8` | no | `USE_154_GDEY`; first render |
| 2026-07-29 | board 1 | `thermometer_c6_release` | none | `cbda104` | no | production build for the first sleep-floor and FC-135 drift datapoints |
| 2026-07-30 | board 1, battery in | `thermometer_c6_debug` | none ×3, `-DUSB_WINDOW_OBSERVE_CYCLES=2` ×1 | `73d4f8a` | no | USB service window tests, `EPD_POWER_GATE` on |
| 2026-07-30 | board 1 | same | none | `aec755b`, then `ac2647e` | no | VBUS wake and LP-IO reclaim fixes |
| 2026-07-30 | board 1, PPK2 at J1 | same | `-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI` | `1d567b6` | no | battery-floor sweep build, ~20 power cycles; nothing reaches the archive (no clock) |
| 2026-07-30 | board 1 | `thermometer_c6_bod_probe` | `-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI` | `6e2fa64` | no | brownout raised 2.51 V (level 7) → ~3.27 V (level 2); flashed through the USB window |
| 2026-07-31 | board 1 | `thermometer_c6_release` | none | `1e1048e` (1027424 B) | no | thresholds 3550 warn / 3500 mV shutdown; brownout, latch and WiFi back to stock; window flash 15.6 s |
| 2026-07-31 | board 1, 400 mAh pack | same | none | `711c3a4` (1027344 B) | yes (1.4 s) | soak start, t=0 ~12:50Z; `DISABLE_LEDS` added (−80 B); pre-erase archive backed up (46 hourly / 19 sparkline / 0 drift, 2026-07-29 14:00Z .. 2026-07-31 11:00Z, base seq 2) |
| 2026-08-05 | `xiao-hat` | `seeed_xiao_esp32c6_epaper_release` | `-DRESYNC_INTERVAL_MIN=43200 -DEXPERIMENT_ARM=3` | `2fa3750` (1008304 B) | no | phase-2 arm 3, vanilla first: resync pinned to 12 h gives ~2 drift samples/day instead of one per 2-3.5 d; archive (231 / 320 / 3) survived byte-for-byte |
| 2026-08-05 | FireBeetle | `dfrobot_firebeetle2_esp32e_release` | `-DULP_ALWAYS_WAKE -DDISPLAY_TEMP_DELTA=999.0f -DREFRESH_EVERY_N_WAKES=60 -DRESYNC_INTERVAL_MIN=43200 -DEXPERIMENT_ARM=1` | `1ea3cd7` (961536 B) | no | phase-2 arm 1: 1440 wakes/day, repaint every 60th, only the refresh count changes at day 14; `USE_154_Z90` + `USE_BMP390L` + `EPD_POWER_GATE` + `DISABLE_LEDS` |
| 2026-08-05 | `xiao-bigscreen` | `seeed_xiao_esp32c6_release` | `-DRESYNC_INTERVAL_MIN=43200 -DEXPERIMENT_ARM=5` | `f5e1749` (1056368 B) | no | phase-2 arm 5; partition-table migration from `44e56b6` (2026-07-06) |
| 2026-08-05 | board 2, no panel | `thermometer_c6_debug` | none | `6338778`, then `0c29c6e` | no | EPD fault path (no panel) |
| 2026-08-05 | board 2 + GDEY0213M21 | same, `RIG=revA-213m21` | none | `fe4c3d5` | no | right-panel control; `ALLOW_RIG_CHANGE=1` |
| 2026-08-05 | board 2 + GDEY0213M21 | same, `RIG=revA-213m21` | `-DEPD_PROBE` | `434436c-dirty` (probe now `27a74f8`) | no | SPI readback probe |
| 2026-08-05 | board 2 + GDEY0213M21 | same, rig `revA-bigscreen` | none | `3326fe7` | no | wrong-panel detection with the tightened threshold |
| 2026-08-09 | board 2, no panel | `thermometer_c6_debug` | `-DDISABLE_DISPLAY -DRESYNC_INTERVAL_MIN=30` | `62320af-dirty` (feature now `57b050d`) | yes ×2 | multi-SSID selection |
| 2026-08-09 | board 2 | same | `-DWIFI_SPIKE` | `e557dd2-dirty` ×4 | | throwaway timing harness, since deleted |
| 2026-08-09 | board 2 | same | `-DDISABLE_DISPLAY -DRESYNC_INTERVAL_MIN=15` | `978f97b-dirty` | yes, before each case | resync backoff |
| 2026-08-11 | board 2 + GDEH0576T81 | `thermometer_c6_debug` | `-DREFRESH_EVERY_N_WAKES=1 -DDISPLAY_TEMP_DELTA=99` | `1620598` (fork `1509966`), `1620598-dirty` (upstream `de82887`), + LUT pin, `dfbbb6d` | no | render-timing A/B, fork retired |
| 2026-08-11 | board 2 | `thermometer_c6_release` | none | `2f22620` | no | baseline for the deployment power captures (`notes.md`) |
| 2026-08-11 | board 2 | `thermometer_c6_debug` | `-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI` | `ccfde51` (bounded, not observed) | no | T81 battery-floor sweep; upload output not captured |
| 2026-08-11 | board 2 | same | `-DFORCE_LUT_TEMPERATURE=<C> -DREFRESH_EVERY_N_WAKES=1 -DDISPLAY_TEMP_DELTA=99` | `3c91183-dirty`, `1fec0e5`, `1fec0e5-dirty`, `7bbe97e` (submodule `bf88c5c`) | no | LUT characterisation |
| 2026-08-11 | board 2 | same | `-DFORCE_LUT_TEMPERATURE=8 -DREFRESH_EVERY_N_WAKES=1 -DDISPLAY_TEMP_DELTA=99` | `1531d1d` | no | left on the cold-LUT arm for the VGH/VGL DMM probe; not deployment-safe |
| 2026-08-11 | board 2 | `thermometer_c6_bod_probe` | `-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI` | `2541adc-dirty` (`.kicad_pro` only) | no | BOD probe at SEL_2, then SEL_3 |
| 2026-08-12 | board 4, then board 3 | `thermometer_c6_debug` | none | `eb5f535-dirty`, `5ce9f19-dirty` | no | first power |
| 2026-08-12 | boards 3 and 4 | `thermometer_c6_release` | none | `753afbc` | yes, both | soak build |
| 2026-08-11 22:4xZ | board 2 | `thermometer_c6_release` | none | `11cd8dd` | yes (1.2 s) | soak build; firmware identical to `753afbc` (`git diff -- src include ulp components platformio.ini sdkconfig.defaults*` empty) |
| 2026-08-12 | board 3 | `thermometer_c6_release` | none | `52cf257` | yes | soak build; same tracked tree as `753afbc`, different gitignored `MY_WIFI_NETWORKS`, dynamic DHCP lease |
| 2026-08-23 | FireBeetle | `dfrobot_firebeetle2_esp32e_release` | `-DULP_ALWAYS_WAKE -DDISPLAY_TEMP_DELTA=999.0f -DREFRESH_EVERY_N_WAKES=5 -DRESYNC_INTERVAL_MIN=43200 -DEXPERIMENT_ARM=2` | `668ff6d` (966624 B) | no | arm 2: repaint every 5th wake (288/day) against arm 1's 60th; wrong `MY_WIFI_NETWORKS` compiled in |
| 2026-08-23 | FireBeetle | same | same | `ef27bd0` (966720 B) | no | arm 2 corrected; 96 B delta is the network strings |
| 2026-08-23 | `xiao-hat` | `seeed_xiao_esp32c6_epaper_release` | `-DDISPLAY_TEMP_DELTA=999.0f -DREFRESH_EVERY_N_WAKES=60 -DRESYNC_INTERVAL_MIN=43200 -DEXPERIMENT_ARM=4` | `49245c9` (1013808 B) | no | arm 4, LP wake pin never reached the LP binary |
| 2026-08-23 | `xiao-hat` | same | same | `cfcc35f` (1013808 B) | no | arm 4 pinned and verified; pin reverted on master in `250a53f` |
| 2026-09-16 | `xiao-bigscreen` | `seeed_xiao_esp32c6_release` | none | `2994f30` (1060960 B) | no | back to production after 42 days of arm 5 |
| 2026-09-16 | `xiao-hat` | `seeed_xiao_esp32c6_epaper_release` | none | `bbc7bd7` (1013936 B) | no | back to production after 24 days of arm 4; vanilla LP binary |
| 2026-09-16 | FireBeetle | `dfrobot_firebeetle2_esp32e_release` | none | `fe3f7cb`, then `68af393` | no | first compensated release; `68af393` adds refit-on-restore |

Boards 1, 2 and 4 are retired to the bench (2026-08-23); board 3 soaks at
another location. Board 2 is bench scratch: erase it freely.

## Harvests

`history.py backup --full`, no flash unless the device-state table says so.
Every backup enters download mode, resets the chip and wipes RTC (boot counter,
in-progress hour, drift window); the archive is untouched.

| Date | Rig | Image | Hourly / sparkline / drift | Span | Base | Header | Panel before the cable |
|---|---|---|---|---|---|---|---|
| 2026-08-05 | `firebeetle` (`44ba5ba`) | `local/archives/hist-firebeetle2_esp32e-8c4db8-2026-08-05.bin` | 254 / 320 / 10 | 2026-07-25 19:00Z .. 2026-08-05 08:00Z (10d13h unbroken) | seq 18, 2026-08-04 21:12:15Z | | `+5063ppm` photographed 2026-08-02, `+5037ppm` 2026-08-05 |
| 2026-08-05 | `xiao-hat` (`431b7b0`) | `local/archives/hist-xiao_esp32c6-fffe16-2026-08-05.bin` | 231 / 320 / 3 | 2026-07-26 19:00Z .. 2026-08-05 09:00Z | seq 12, 2026-08-04 13:40:35Z | `built 8712f72`, orphaned | hash confirmed on panel |
| 2026-08-23 | rev A board 2, day 11.6 | `local/archives/hist-revA-board2-20260823.bin` (1966080 B) | 279 / 320 / 3 | 2026-08-11 22:00Z .. 2026-08-23 12:00Z | seq 14, 2026-08-23 00:38:03Z, cursor 0x001100 | `formatted by 11cd8dd`, created before first sync, `last snapshot 11cd8dd` | `#498 r347 lp16737 11d14h w:ULP mx4.0V 11cd8dd Aug12'26 s4d`, 3964 mV, 23.0 °C |
| 2026-08-23 | rev A board 4, day 11.6 | `local/archives/hist-revA-board4-20260823.bin` | 279 / 320 / 3 | same as board 2 | seq 13, 2026-08-22 23:05:57Z, cursor 0x0010f0 | `formatted by 753afbc`, `store created 2026-08-11 22:24:26Z` | `#504 r341 lp16747 11d15h w:ULP mx4.0V 753afbc Aug12'26 s4d`, 3962 mV, 22.9 °C |
| 2026-08-23 | rev A board 1, day 23.0 | `local/archives/hist-revA-board1-20260823.bin` | 554 / 320 / 4 | 2026-07-31 12:00Z .. 2026-08-23 13:00Z | seq 26, 2026-08-23 14:01:23Z, cursor 0x002320 | `formatted by 711c3a4`, `store created 2026-07-31 12:48:12Z`, no `last snapshot` field | `#1392 r1094 lp33113 22d23h w:ULP mx4.2`, 4086 mV, 22.8 °C |
| 2026-08-23 | `xiao-bigscreen`, arm 5 day 18.1 | `local/archives/hist-arm5-xiao-t81-20260823.bin` | 435 / 320 / 32 | 2026-08-05 11:00Z .. 2026-08-23 13:00Z | seq 35, 2026-08-23 07:50:35Z, cursor 0x001ec0 | `formatted by f5e1749`, `last snapshot f5e1749` | `! EXP 5 60s`, `#1763 r1596 lp26499 18d2h w:ULP mx4.3V f5e1749 Aug5'26 s6h`, 23.5 °C |
| 2026-08-23 | `firebeetle`, arm 1 day 18.1 | `local/archives/hist-arm1-firebeetle-20260823.bin` | 691 / 320 / 45 | 2026-07-25 19:00Z .. 2026-08-23 13:00Z | seq 54, 2026-08-23 09:31:07Z, cursor 0x003080 | `formatted by 44ba5ba`, `last snapshot 1ea3cd7` | |
| 2026-08-23 | `xiao-hat`, arm 3 day 18.1 | `local/archives/hist-arm3-xiao-hat-20260823.bin` | 667 / 320 / 20 | 2026-07-26 19:00Z .. 2026-08-23 13:00Z | seq 41, 2026-08-23 08:38:10Z, cursor 0x002bd0 | `formatted by 8712f72 (!! unknown to this repo)`, `last snapshot 2fa3750` | |
| 2026-09-16 | `firebeetle`, arm 2 day 23.7 | `local/archives/hist-arm2-firebeetle-20260916.bin` | 1261 / 320 / 92 | | seq 101 | `formatted by 44ba5ba`, `last snapshot ef27bd0` | `! EXP 2 60s/RESYNC/REFRESH`, `! DRIFT +210s/12h +4799ppm n6 +-1%`, 3688 mV, `#34541 r6918 lp0 23d17h` |
| 2026-09-16 | `xiao-hat`, arm 4 day 23.7 | `local/archives/hist-arm4-xiao-hat-20260916.bin` | 1237 / 320 / 63 | | seq 88 | `formatted by 8712f72 (!! unknown)`, `last snapshot cfcc35f` | `! EXP 4 60s/RESYNC/REFRESH`, `#34442 r593 lp34441 23d16h` |
| 2026-09-16 | `xiao-bigscreen`, arm 5 day 42.1 (23.7 since the August RST) | `local/archives/hist-arm5-xiao-t81-20260916.bin` | 1005 / 320 / 78 | | seq 81 | `formatted by f5e1749`, `last snapshot f5e1749` | `! EXP 5 60s`, `#2187 r1936 lp34688 23d18h … s4h` |

Per-arm record counts: arm 1 image 10 at `arm`=0 + 35 at `arm`=1; arm 3 image
3 at 0 + 17 at 3; 2026-09-16 FireBeetle 10 / 35 / 47 (arms 0 / 1 / 2); hat 3 /
17 / 43 (arms 0 / 3 / 4); T81 78 all arm 5. Rev A soak images are `arm` = 0
throughout. Pair headline from the 2026-08-23 harvest: −19.7 ppm (board 2) against
−6.6 ppm (board 4), a 3.3σ part-to-part gap, with the 279 overlapping hourly rows
agreeing to +0.003 °C mean. Drift analysis: [`docs/clock-drift.md`](clock-drift.md).

## Results

One line per experiment. Rows with a section name have detail below.

| Date | Result | Finding | Detail |
|---|---|---|---|
| 2026-07-25 | PASS | Relocation to the new table: `factory` 0x10000/3968K confirmed by `read_flash 0x8000`, app now at 0x1f0000, first boot formatted and wrote `base snapshot seq 1 (0 hourly, 1 sparkline, cursor 0x000010)` | |
| 2026-07-25 | PASS | `history.py backup` at 921600 over the CH340 read the right identity; incremental read 24576 bytes, not 1920 KB | |
| 2026-07-25 | PASS | Sparkline accumulates 1 → 3 → 6 → 8 over ~7 min (one record per refresh on \|Δtemp\| ≥ 0.1 °C, ambient ~28.5 °C with the sensor 15 cm off-board); hourly path confirmed at 15:00Z: `1 hourly` for 14:00Z at 29.0/29.2/29.1 °C, min/max/avg distinct | |
| 2026-07-25 | PASS | Reflash keeps history: `RTC history version mismatch — resetting history` then `History restored: 0 hourly, 8 sparkline (base seq 1, +0/7 replayed)`, captured from byte zero via `--after no_reset` + manual reset | |
| 2026-07-25 | PASS | Restore after RTC loss (DTR/RTS reset reads `rst:0x1 (POWERON_RESET)`, boot_count back to 1): 6 sparkline points spanning two flashes | |
| 2026-07-25 | PASS | Format 2 (hourly-only journaling) re-formats on first boot; `History restored: 0 hourly (+0 replayed), 9 sparkline, base seq 13` | |
| 2026-07-25 | PASS | Synthetic injection and both charts verified from flash | Injection |
| 2026-07-25 | PASS | Restore keeps its anchor and fills the outage with `HOURLY_NO_DATA` (`1f6552d`) | Restore anchor |
| 2026-07-25 | PASS | A format bump leaves the archive intact and disabled (`19dde9f`) | Format bump |
| 2026-07-25 | BUG | Journal rebuild boot-looped on the task watchdog; fixed; rebuild measured 2444 ms | Journal rebuild |
| 2026-07-25 | BUG | `drift_state_load()` trusted flash: injected `resync_interval_s = 0` would bring up WiFi every wake; clamped | Drift state load clamp |
| 2026-07-26 | note | `xiao-hat`: probe the XIAO's BAT pads, not the hat's JST2 (0.2 ms ~14 mA inrush, then nothing); BAT-pad floor bypasses the ETA9740 (~330-500 µA); compare with 22 µA @ 4.2 V in `notes.md` | |
| 2026-07-26 | PASS | Plausibility gate and unattended sensor recovery on the C6 | Sensor fault |
| 2026-07-26 | BUG | LP counters do not survive `ulp_lp_core_load_binary()`; a preserved delta reference stranded a repaired sensor | Sensor fault |
| 2026-07-26 | note | Pre-gate readings reached flash: 127.5 °C (erased, `2d90340`) and 0.0 °C (left in place, one point) | Sensor fault |
| 2026-07-26 | CONSTRAINT | On the C6 the CPU cannot use the sensor bus once the LP core owns it | LP I2C |
| 2026-07-26 | PASS | Fault rendering: `--.-` + `! SENSOR`, `r2` across 31 wakes, `lp30 e30 u30`, `! LP W 0x108`; two unattended fault/recovery cycles without power cycling | Sensor fault |
| 2026-07-26 | note | `431b7b0` archive empty (0 / 0 / 0): every reflash wiped RTC, so no run spanned an hour boundary. Recording path with rejected readings still unverified at the storage layer | |
| 2026-07-29 | PASS | rev A board 1 first power: no 32k-XTAL fallback warning, BMP581 ID 0x50 / 29.79 °C on LP I2C, 4196 mV float-held, base seq 1 (erase 4 / program 12 / verify 4 ms), deep sleep entered | |
| 2026-07-29 | PASS | Board 1 first render: 33.9 °C (29.8 °C an hour earlier: USB self-heat plus bench sun, unquantified), `4204mV`, footer `#3 r3 lp2 0d w:ULP mx4.2V 91bd4d8`; `#3 r3` proves archive continuity across the reflash; boost chain works on 0.47 Ω / 10 µH | |
| 2026-07-30 | PASS | USB flash-service window, VBUS wake, LP-IO pad reclaim, IDF-14951 clock gate cleared | Board 1 USB window |
| 2026-07-31 | flash | Board 1 soak start | Board 1 soak |
| 2026-08-05 | PASS | Drift journal is uncapped (10 records vs `DRIFT_PPM_HIST_SIZE` 6) and reproduces the panel: 5063 / 5038 ppm recomputed vs `+5063ppm` / `+5037ppm` photographed (1 ppm of integer truncation) | |
| 2026-08-05 | PASS | Failed resyncs are recoverable from window lengths (hat window 2 = 4.017 d against a 2 d setting: one miss ~2026-07-29) | |
| 2026-08-05 | note | Header `built` hash records the formatting build, can be orphaned (`8712f72`) | Header timestamp |
| 2026-08-05 | PASS | Phase-2 arms flashed; `! EXP` badge and per-record `arm` tag proven | Phase-2 arm flashes |
| 2026-08-05 | note | First drift record of every arm straddles the regime change; discard | Phase-2 arm flashes |
| 2026-08-05 | note | Three hashes for one firmware (`2fa3750` / `1ea3cd7` / `f5e1749`); FireBeetle's `1ea3cd7` inferred from the timeline, not read off its panel | Phase-2 arm flashes |
| 2026-08-05 | PASS | `EPD_POWER_GATE` mandatory on every DESPI-C02 rig; `DISABLE_LEDS` mandatory on the ESP32-E | Phase-2 arm flashes |
| 2026-08-05 | PASS | Dead-panel detection on board 2: 91213 ms / 18001 slices / 9 timeouts, LED blink | EPD fault |
| 2026-08-05 | BUG | Upload gate hook did not run (silent); rekeyed on `COMMAND_LINE_TARGETS`, refuses in 0.99 s | Upload gate |
| 2026-08-05 | PASS | BUSY detection limits measured three ways; wrong panel caught only after the threshold change | EPD fault |
| 2026-08-05 | PASS | UC8151 readback obtained: `0x70` → `01 0e 00 00` driven | EPD readback |
| 2026-08-09 | PASS | Multi-SSID selection, hint rewrite, RSSI pick; `RESYNC_INTERVAL_MIN` clamp trap; RTC `self_addr` forward path exercised | WiFi |
| 2026-08-09 | PASS | WiFi timing spike: scan 2501 ms at 120 ms/channel, association ~300 ms, DHCP 2.2-4.6 s | WiFi |
| 2026-08-09 | PASS | Resync backoff escalates only on evidence of absence | WiFi |
| 2026-08-11 | PASS | First T81 drive on rev A; fork and upstream agree at equal LUT; LUT selection was ~48% of busy time | T81 driver comparison |
| 2026-08-11 | STATE | Baseline `2f22620` for the power captures; `PPK2_DEBUG` and forced-cadence flags withdrawn | Power baseline |
| 2026-08-11 | STATE | T81 battery-floor sweep: 11 of 13 steps, cliff bracketed 3400-3300 mV | Power baseline |
| 2026-08-11 | PASS | Five LUT codes timed, ~1.95x cliff at ≤10 °C, two firmware bugs found | T81 LUT characterisation |
| 2026-08-11 | STATE | Board 2 left on forced 8 °C for the VGH/VGL DMM probe | T81 VGH/VGL probe setup |
| 2026-08-11 | PASS | BOD probe at SEL_2 boot-loops under the T81 at 4.23 V in; SEL_3 clean | BOD probe |
| 2026-08-12 | PASS | Boards 3 and 4 first power; fleet render timing 229 ± 1 slices | Boards 3 and 4 |
| 2026-08-12 | STATE | Soak builds on boards 2, 3, 4; board 2's cycle proved, boards 3/4 inferred from the boot counter | Soak start |
| 2026-08-12 | PASS | Board 3 NTP-synced at first boot; its ~190 mV pack gap explained by charge state, not divider spread | Soak start |
| 2026-08-23 | PASS | Published +5066 ppm (E) and +305 ppm (hat) round-trip through no-erase reflashes | Published figures re-decoded |
| 2026-08-23 | flash | Arm 2 crossover; first upload carried the wrong network list | Arm 2 |
| 2026-08-23 | BUG | Arm 4's LP wake pin did not reach `ulp_main.bin`; no gate inspects the LP binary | Arm 4 LP pin |
| 2026-09-16 | PASS | Compensation armed at first boot on the FireBeetle: footer `c+4820` | Return to production |

### Injection (2026-07-25)

`hstest --inject <size> <mac> <now> <file>` builds a full 1920 KB image with the
real store code, filled from `MockData.h`, stamped with the board's MAC.
`history.py restore` accepted it; the device came up
`History restored: 720 hourly (+0 replayed), 62 sparkline, base seq 1` and read
back 720 rows spanning 2026-06-25 15:00Z .. 2026-07-25 14:00Z.

| Check | Injected | On the panel |
|---|---|---|
| 30-day chart | coldest day 2026-07-08, 19.3 °C daily avg; daily aggregates 16.8-26.1 °C | dip "around July 8", 24 °C gridline |
| 24 h sparkline (`--inject … ramp`) | 10.0 → 30.0 °C diagonal at fixed 30 min spacing, 48 points 1800 s apart (100 → 300 ×10) | clean diagonal |

Two earlier "faults" on the mock sparkline were not: the flat stretch up to 0h is
`MockData.h`'s 6 h carry-in (21:41Z = 23:41 CEST), and >1 point/hour is correct
because the 24 h chart records per refresh.

### Restore anchor and outage fill (2026-07-25, `1f6552d`)

Injected a 30-day archive whose newest hour was 2026-07-22 17:00Z
(`hstest --inject 1966080 <mac> $(date +%s)-259200`), booted `f050bfc`, synced
at 2026-07-25 18:55:51Z. Read back 792 hourly rows: the 720 injected ones still
dated 2026-06-22 18:00Z .. 2026-07-22 17:00Z, then 72 contiguous
`HOURLY_NO_DATA` rows ending at the in-progress hour. Decoding the base ring
alone: anchor moved 2026-07-22 17:00Z → 2026-07-25 17:00Z, newest real entry
stayed at 2026-07-22 17:00Z (24.7 / 24.9 / 24.8 °C), ring rolled 72 h. The old
code moved the anchor with no fills, re-dating all 720 readings 3 days forward.

### Format bump (2026-07-25, `19dde9f`)

`HS_FORMAT` 2 → 3 with nothing else changed. Boot log:
`HistoryStore: on-flash format 2, firmware speaks 3 — archive left intact and DISABLED. Back it up (tools/history.py backup), then erase_flash to start a new one.`
No format, no restore, no base write on that boot or the two after. Partition
byte-identical: sha256 `bd49a1a6…c774b2`, 1966080 bytes, `cmp` clean. The
"before" image was read with `--after no_reset` so a cold boot could not append
a record and confound the hash. `history.py backup --full` still decoded the
disabled archive (792 hourly).

### Journal rebuild (2026-07-25, BUG)

Result: rebuild of 720 hours from 720 journal records takes **2444 ms**, then
`sparkline backfilled with 24 hourly points`, then a normal boot, no watchdog.
Before the fix a slot-by-slot scan made ~119k `esp_partition_read` calls per
pass and blew the 5 s task watchdog (`task_wdt: IDLE0 (CPU 0)` → panic → reboot)
on every cold boot without a base, i.e. every boot after `erase_flash`. On the
bench it looked like a stale frame plus `base (none — journal only)` in the
backup. Fix: 512-byte chunks, all-0xFF chunks skipped without CRC, yield to
IDLE0 every 256 chunks. `tools/hstest` now bounds flash calls (fails at
`2051 flash reads over 2048 slots`). The 2444 ms is ~3x the estimate that
replaced a 10x-wrong one; dominated by ~320 µs per 512-byte read. A full journal
adds CRC over ~122k slots per pass.

### Drift state load clamp (2026-07-25, BUG)

An injected `resync_interval_s = 0` put `next_resync_time` on `now`, so every
wake would have brought up WiFi (1.5-4.5 C per failed attempt). Now clamped;
drift samples with a zero window are dropped instead of inflating `nN`. Badge
went `+0ppm n1` → `-5265ppm n1`.

### Sensor fault handling on the C6 (2026-07-26, `xiao-hat`)

Ground pulled with the device running. Early gate build (`-dirty`,
`seeed_xiao_esp32c6_epaper_release`): panel `--.-` with `! SENSOR`, status
`#5 r2 lp1 u4 0d w:ULP mx4.3V`, two refreshes across five wakes, `u4` climbing
once per wake (a NACKing sensor: both LP I2C error paths wake the CPU, so a dead
bus costs one wake and one LP reload per `SLEEP_INTERVAL_S`; left unbounded).

Two bugs: `ulp_lp_core_load_binary()` memsets the whole
`CONFIG_ULP_COPROC_RESERVE_MEM` region, so LP counters read `lp1` after nine
reloads; they are now saved and written back around the load. Preserving
`prev_temp_c` across the reload then stranded a repaired sensor: the value
latched from the floating bus sat within `TEMP_DELTA_THRESHOLD_C` of the room, no
delta fired, the panel stayed blank until hand-warming. `prev_temp_c` is not
preserved.

Debug build (`seeed_xiao_esp32c6_epaper_debug`): the driver refuses a part that
does not answer with its chip ID, so the 127.5 °C an undriven bus produces
(`temp: 127.498032` on the earlier build) is never formed. `r2` across 31 wakes
(boot frame plus the `FAULT_REPAINT_WAKES` heartbeat), `lp30 e30 u30`, and
`! LP W 0x108` (LP core, trigger write, `ESP_ERR_INVALID_RESPONSE`). Fault →
recovery → fault → recovery ran twice unattended, recovery through the
coprocessor; a rule that refused a coprocessor reading during a fault made
recovery impossible on the C6 and was reverted.

Two pre-gate readings reached flash: 127.5 °C (archive erased, `2d90340`) and a
0.0 °C from a raw `0x000000` (left in place: one point, archive only a day old).
Open: hourly entries and `HOURLY_NO_DATA` for a fully rejected hour are still
unverified at the storage layer.

### LP I2C pin ownership (2026-07-26, CONSTRAINT)

`lp_core_i2c_master_init()` calls `rtc_gpio_init()` on GPIO6/7, setting
`LP_AON_GPIO_MUX_SEL` and taking the pads out of the digital domain, where
`i2c_new_master_bus()` cannot reach them. Measured: with ground reseated the LP
core read the sensor on 28 of 30 cycles (`lp30 e2`) while every CPU read failed
and the panel stayed `--.-`. `ulp_lp_core_stop()` touches no GPIO register. Two
inferred hand-back paths, untested here: `rtc_gpio_deinit()` on both pins (the
ESP32-E path; on C6 it also force-disables the shared LP IO clock gate, IDF TODO
IDF-14951), or opening the HP bus on the LP_I2C port (`port >= SOC_HP_I2C_NUM`).
`verify_ulp_temp()`'s direct re-read has therefore likely never worked on this
board. Verified against ESP-IDF v6.0.1 source. The 2026-07-30 board 1 rows
record the reclaim working intermittently.

Serial cannot be captured on wakes on this rig (USB-Serial-JTAG re-enumerates;
DTR reaches GPIO9): read the panel counters instead. Procedure in
`/device-session`.

### Board 1 USB service window (2026-07-30, `73d4f8a` → `ac2647e`)

Result: hands-free reflash works and the GPIO4 VBUS wake is proven. Battery
attached (3770 mV), panel seated, `thermometer_c6_debug`.

| Check | Observed |
|---|---|
| Window open | `! USB` badge; port enumerated 45 s / 45 s vs ~1 s on / 4 s off while sleeping |
| Hands-free reflash | two back-to-back at ~18 s each, board returns to the app |
| `-DUSB_WINDOW_OBSERVE_CYCLES=2` | exactly two deep sleeps, then the window; `USB host attached, but this sleep is an observe cycle`; `Sleeping with ULP wakeup (timer safety net: 5 s)` |
| Continuous serial | six consecutive cycles on one port, no re-enumeration |
| VBUS wake (`aec755b` / `ac2647e`) | unplug: `! USB` cleared within one refresh (~300 ms debounce); replug: back in ~2 s; window held 25 / 25 s |
| Replug after ≥9 min asleep on battery | 20:15:12 replug, port at 20:15:13 (~1 s); the sleep was entered after `rtc_gpio_deinit()` had run, so IDF-14951 does not break the GPIO4 wake |
| LP-IO pad reclaim | 5 resets while the LP core owned the bus: 3 hit `Chip ID read failed — reclaiming I2C pads from the LP domain and retrying` then `BMP581 detected (chip ID 0x50)`, 2 read first time; `failed to read BMP58x chip ID` never occurred |

Findings: a manual BOOT+RST park leaves the chip in ROM download mode after
`pio upload` (`rst:0x15 (USB_UART_HPSYS),boot:0x10 (USB_BOOT)`,
`wait usb download`) and needs a physical RST; flashing through the window does
not. esptool `--after watchdog_reset` is unsupported on the C6. The host probe
is marginal against Linux USB autosuspend (`power/control=auto`, 2000 ms): a
slow boot logged `charger, not a bus` and the window opened ~50 s later at r14.
The first frame after a reflash rendered `--.-` + `! SENSOR` on `73d4f8a` (LP-IO
mux still routed across the reset); on `ac2647e` both post-flash frames carried
a real temperature. Sensor 33.7 °C flat while charging, ~33.5 °C parked in the
window: self-heat, not ambient.

Open: sleep floor with the GPIO4 wake armed against the 18.7 µA baseline
(measured later, `notes.md`).

### Board 1 soak start (2026-07-31, `711c3a4`)

Getting in took a manual BOOT+RST park: VBUS was already high off a dumb
charger, so the plug-in wake at 14:38:08 CEST probed, missed SOF and classified
`charger, not a bus` (second sighting of the autosuspend-marginal probe),
costing the service window until the 1 h safety net. Backup → erase → upload
chained on the by-id node; `store created 12:48:12Z` is ~5.5 min after the
upload, i.e. the RST press. Post-flash backup: base seq 1, 0 hourly / 1
sparkline / 0 drift, identity `GDEM0154I61/BMP58x` (the pre-erase header still
said `GDEW029I6FD`, a fossil of the 2026-07-29 format). Panel live with `! USB`,
no `! NOSYNC`. Soak t=0 = the verify backup's reset, ~12:50Z; USB out afterwards
is a supply handover, not a power cycle. Pre-erase image: session scratchpad
`board1-prereset-20260731.bin`.

### Phase-2 arm flashes (2026-08-05)

Result: `EXPERIMENT_ARM` reaches the panel (`! EXP 1 60s`, `! EXP 3 60s`,
`! EXP 5 60s`) and the journal; a no-erase reflash preserved the hat's 231 / 320
/ 3 byte-for-byte across the arm change, with old records decoding `arm=0`.

Arm 3 (hat, `2fa3750`): the panel held its pre-flash frame after the upload
because the chip was still parked from the morning's harvest; an enumeration
watch showed UP while parked, DOWN at t+146 s (RST), UP at t+148 s, DOWN at
t+156 s, i.e. an ~8 s boot → NTP → render → sleep. A parked C6 stays enumerated;
a healthy one drops off the bus within seconds (now in `/device-session`).

Arm 5 (`xiao-bigscreen`, `f5e1749`): partition-table migration verified by
reading 0x8000 before (`factory` 0x10000/3968K, no `history`, coredump 0x3f0000)
and after (`history` 0x10000/1920K, `factory` 0x1f0000/2048K), no `erase_flash`.
The rig's previous build `44e56b6` (2026-07-06) predates the partition, so its
five photographed drift samples in `clock-drift.md` are its only earlier record.
Verification backup not taken: the board dropped back to sleep between
enumerating and pyserial asserting RTS (`OSError: [Errno 71] Protocol error`);
archive health taken from the absence of `! NOARCH`.

Arm 1 (FireBeetle, `1ea3cd7`): two config facts. `EPD_POWER_GATE` is mandatory
on every DESPI-C02 rig: the adapter draws ~534 µA quiescent, the FDN340P gate
(GPIO13/D7 on the E, GPIO17/D7 on the plain C6, `src/Display.cpp:47-56`,
`docs/wiring.md`) has a 10k pull-up holding the P-FET off at reset, so an
ungated build leaves the panel dark with no diagnostic; the E's 19.4 µA floor
needs the gate, ungated the rig is ~562 µA; only the Seeed hat `#undef`s it
(`src/Display.cpp:21`). `DISABLE_LEDS` is mandatory on the ESP32-E: the build
fails on a missing `Adafruit_NeoPixel.h`, never vendored at the espidf
migration.

First drift record per arm: `drift_state_load()` restores `resync_interval_s`
and clamps it into `[RESYNC_INTERVAL_MIN, RESYNC_INTERVAL_MAX]`, so a stored
86400 s survives a 43200 s override and
`next_resync_time = last_sync_time + resync_interval_s`
(`src/Thermometer.cpp:1077`) schedules the first attempt on the old cadence.
FireBeetle arm 1's lands ~2026-08-05 21:11Z with a ~24 h window, the hat's arm 3
~2026-08-06 01:00Z with ~3.5 d; both carry the new arm byte. Discard the first
record per arm, including at the day-14 crossover.

Three hashes for one firmware: rows were committed between flashes, so hat
`2fa3750`, FireBeetle `1ea3cd7`, big screen `f5e1749`;
`git diff 2fa3750 f5e1749 -- src include ulp components platformio.ini` is
empty. The FireBeetle's row first said `2fa3750`; `1ea3cd7` is inferred from the
commit timeline (its `last snapshot written by 1ea3cd7` at the 2026-08-23
harvest confirmed it).

### EPD fault path (2026-08-05, board 2)

Result: a dashboard render into no panel takes **91213 ms across 18001 busy
slices**, nine GxEPD2 timeouts at 10 s (91256 / 18009 on `6338778`, repeatable
to 0.05%), ~5x a healthy render; the fault latches on boot 1 and later wakes log
`temperature hasn't changed significantly` with no render. Before this change
`_waitWhileBusy` returned void and printed `Busy Timeout!` only to a console
`DISABLE_SERIAL` removes. LED pattern three short-short-short-long groups,
pause, repeat; the blink ignores `DISABLE_LEDS`. Sensor and archive unaffected
(`BMP581 detected (chip ID 0x50)`, 30-31 °C USB self-heat, base seq 1). Battery
read 4202-4250 mV with no pack (charger holding VBAT).

Where BUSY detection stops, GDEY0213M21 spare (`USE_213_M21`, added 2021-11-26
in `361248f`) on the 24-pin FPC, JP2 0.47 Ω + JP5 10 µH:

| Panel | Rig | Render | Verdict |
|---|---|---|---|
| none | `revA-bigscreen` `0c29c6e` | 91213 ms / 18001 slices / 9 timeouts | `BUSY STUCK`, caught |
| wrong (2.13" on the T81 driver) | `revA-bigscreen` `0c29c6e` | 21281 ms / 4016 slices / 2 timeouts | no fault; garbage patterns on glass |
| right | `revA-213m21` `fe4c3d5` | 3692-3900 ms / 725-726 slices / 0 timeouts | healthy |
| wrong, tightened threshold | `revA-bigscreen` `3326fe7` | `21400ms, 4016 busy slices *** BUSY STUCK ***` | caught, LED blinking |

BUSY liveness proves the controller clocks, not that pixels changed. The
threshold is now 2x the panel's own GxEPD2 busy timeout (20 s here, 40 s on a
Z90 whose healthy full refresh the source quotes as both ~15 s and ~21 s against
its 20 s limit, `notes.md`); a flat 30 s would have false-latched a cold Z90. A
wrong panel that answers every wait still passes, and two panels sharing a
controller and resolution are indistinguishable without an OTP identifier
(`0x38` on SSD1681, `0x70` on UC8151, `hardware/datasheets/README.md`). The
panel hash `fe4c3d5` read as `fe4c3d9` off the damaged glass: treat a
one-character discrepancy as a read error first. `ALLOW_RIG_CHANGE=1` was needed
to flash `revA-213m21` over a `GDEH0576T81` header; the gate logged
`carries GDEH0576T81 — matches rig revA-bigscreen` on the `3326fe7` flash.

### Upload gate (2026-08-05, BUG)

`scripts/upload_gate.py` refuses to flash a rig whose panel disagrees with the
`history` header the board carries. Registered via
`env.AddPreAction("upload", cb)` it never ran and printed nothing: the bare
string resolves to a SCons File node nothing builds, `env.Alias("upload")`
creates a fresh empty alias, and PlatformIO registers `upload` with
`AddPlatformTarget` after every extra script has run. Two wrong-rig images
(`RIG=revA-smallscreen` onto a `GDEH0576T81` archive) flashed in silence. Fixed
by keying off `COMMAND_LINE_TARGETS`, which also moves the refusal before the
~60 s compile: aborts in 0.99 s. All three paths verified: mismatch refused with
the `RIG=revA-smallscreen` hint, `ALLOW_RIG_CHANGE=1` proceeds, match prints
`carries GDEH0576T81 — matches rig revA-bigscreen`. Offline coverage
(`python3 scripts/upload_gate.py <archive.bin>`) passed throughout. A guard
whose failure mode is silence must be tested by making it fail.

### EPD readback (2026-08-05, board 2 + GDEY0213M21, `-DEPD_PROBE`)

`display_probe_readback()` sends a command, turns MOSI into an input and
bit-bangs eight clocks twice, once against a pulldown and once against a pullup;
a floating line follows its pull, a driven one reads the same both ways. Stable
across three renders: `0x70` → `01 0e 00 00`, `0x71` → `13 13`, `0x40` →
`d2 00`, all driven; foreign SSD168x commands `0x2f` / `0x1c` and a no-op split
`00` / `ff`, floating. `0x70` is a candidate panel identifier. This corrects
`6338778`'s claim that readback needs no rev B wiring change: `SSD1677.pdf`
Table 6-1 gives 4-wire SPI a separate SDO pin, BS is strapped low (DESPI-C02 R4
3 Ω → GND) and the 24-pin FPC carries no SDO, so the T81 most likely has no
return path (untested). `GxEPD2_576_GDEH0576T81::_Init_Full` reads controller
temperature via `0x40`, gets 0, and picks the coldest LUT; do not "fix" by
enabling `_readData` until a T81 is probed. Open: `0x40` → `d2` does not match
~33 °C, and the probe samples on SCK high where SSD1677 shifts on the falling
edge (possible one-bit offset); needs the UC8151D datasheet. Rev B discussion:
`hardware/thermometer-c6/README.md`.

### WiFi (2026-08-09, board 2, no panel)

Multi-SSID (`62320af-dirty`, now `57b050d`,
`-DDISABLE_DISPLAY -DRESYNC_INTERVAL_MIN=30`): first boot
`scan 2501ms, 12 APs, best '<hotspot>' at -42 dBm` over `<house-ap>` at −56;
later resyncs connect with no scan line; with the hinted AP killed,
`'<hotspot>' refused us (reason 201)` → `falling back to a scan` →
`best '<house-ap>' at -56 dBm`, hint rewritten. Reason 201
(`WIFI_REASON_NO_AP_FOUND`) is terminal, so no 8 s hint timeout. Miss duration
unmeasured (timestamps stripped from the capture); assume a double sweep.
`RESYNC_INTERVAL_MIN` sets only the clamp floor while the live interval is
restored from the base snapshot, so a stored 86400 survived
`-DRESYNC_INTERVAL_MIN=30` and no resync fired until `erase_flash` (cost two
capture cycles; the mirror of `.claude/rules/history-store.md`'s injected-zero
hazard). Adding one `RTC_DATA_ATTR` byte tripped the `self_addr` check
(`RTC history version mismatch — resetting history`) and recovered 99 hourly (+1
replayed), 3 sparkline from flash: the `.claude/rules/rtc-state.md` forward
path.

Timing spike (`e557dd2-dirty`, `-DWIFI_SPIKE`, four flashes; durations only, no
PPK2): scan 2501 ms at the IDF default 120 ms/channel (n=8, zero variance), 1801
at 60, 1601 at 40, ~1.2 s fixed; association 295-335 ms (n=15) pinned or not;
DHCP 2.2-4.6 s, ~90% of a connect, 2841 ms after dropping the ARP conflict check
(`62320af`); scans return 5-14 APs for identical conditions. Write-up:
[`notes.md`](notes.md).

Backoff (`978f97b-dirty`, `-DDISABLE_DISPLAY -DRESYNC_INTERVAL_MIN=15`, archive
erased before each case): absent network (SSID powered off) →
`refused us (reason 201)` → `falling back to a scan` → `none of ours` →
`WiFi failed (2 in a row, network absent), retrying in 60 s`, then 120 s, flat
at 120 s (8x the 15 s floor). Present but unusable (wrong password) →
`refused us (reason 202) — check the password in local-secrets.h`, retry flat at
15 s across seven failures. Both signals must agree (driver sweep and full scan)
because scan presence is noisy. No RTC state added; ESP32-E headroom unchanged
at 32 bytes. Open: tier-0 miss duration. A phone hotspot self-disables after
minutes with no client.

### T81 driver comparison, fork vs upstream (2026-08-11, board 2)

Result: stock upstream GxEPD2 and the fork agree to 0.66% of busy slices at
equal LUT; the fork's ~48% extra busy time was LUT selection. Flags
`-DREFRESH_EVERY_N_WAKES=1 -DDISPLAY_TEMP_DELTA=99` (`src/Thermometer.cpp:109-115`),
upload gate clean on all four flashes, 21-25 renders per config.

| Driver | LUT | Busy slices (sd) | Wall time mean | Steady state |
|---|---|---|---|---|
| fork (`1509966`) | `0xE8` | 445.62 (0.50) | 3098 ms | ~3075 ms |
| upstream (`de82887`), LUT pinned | `0xE8` | 442.67 (0.48) | 3034 ms | |
| upstream, own default | `0xF1` | **228.25** (0.44) | 1960 ms | ~1935 ms |

Means include the first post-reset render, ~500 ms long. Both drivers read panel
temperature via `0x40` + `_readData()`, which returns 0 here; the fork falls
through `temp <= 5` to the coldest waveform, upstream guards it
(`if (temp == 0) return 241`, the 20..30 °C band). Every T81 refresh figure
recorded before this date, including the readme's ~45 mC XIAO+T81 row, was taken
on the coldest LUT. Rotation: upstream drives PSR `0x2F` where the fork used
`0x27` plus `_reverseByte`, so `DISPLAY_ROTATION 2` (`dfbbb6d`) corrects a 180°
frame at no cost. All six panel drivers build against upstream (Z90, M09, M21,
I6FD, GDEY0154D67, T81).

Hardware: the T81 ran on the factory JP2 0.47 Ω + JP5 10 µH (third controller
family on the universal config; evidence for deleting L2/R15/R16 in rev B). Its
FPC contacts are on the back face, so J4's dual-contact `FPC-05FB-24PH20` is
required. BMP581 read 32.57 °C against ~26 °C ambient while USB-powered with a
charging pack (~6.5 °C self-heat, crossing the 30 °C LUT band). Board 2's prior
state was `978f97b-dirty` rendering normally, an unlogged flash.

### T81 LUT characterisation (2026-08-11, board 2, `-DFORCE_LUT_TEMPERATURE`)

Result: a ~1.95x cliff at the ≤10 °C boundary, flat either side; two firmware
bugs found by measuring. `-DFORCE_LUT_TEMPERATURE=<C>` bypasses the VBUS gate and
raises `! LUT`; battery and USB; 7-20 renders per code, zero faults; hashes
`3c91183-dirty`, `1fec0e5`, `1fec0e5-dirty`, `7bbe97e` (submodule `bf88c5c`).

| Forced code | Slices | Wall time |
|---|---|---|
| 232 | 443 | 3012 ms |
| 235 | **447** | 3030 ms |
| 238 | 238 | 1989 ms |
| 241 | 228 | 1935 ms |
| 244 | 225 | 1925 ms |

0 °C costs no more than 8 °C.

| Symptom | Cause | Fix |
|---|---|---|
| First build read 228 slices at a forced −5 °C, i.e. no effect | `PANEL_HAS_LUT_TEMPERATURE` tested in `Display.h` before `app_common.h` supplied `USE_*`; both entry points compiled to stubs, build clean | include `device-config.h` from `Display.h`, `#error` in `Display.cpp` after all includes (`c2d3ad6`, +342 B) |
| With the value reaching the panel, every render after the first failed, `DISPLAY_FAULT_BUSY_IDLE` latched | the `setTemperature()` patch skipped `_writeCommand(0x40); delay(5); _readData()` in `_InitDisplay()`; reproduced on battery + USB (2504 ms / 228 then 797 ms / 0) and J1 open (2497 / 795) | issue the read unconditionally, substitute only the value (`7bbe97e`, three-line driver diff) |

Controls: calls compiled out, 20 renders / 0 faults; first patch at either LUT,
1 render then a latched fault; corrected patch, 19-20 renders / 0 faults at 443
slices. `BUSY_IDLE` vs `BUSY_STUCK` separated "never woke" from "hung". The
first bug would not have shown in service: the 241 fallback is right at room
temperature, so the feature was missing only in the cold.

### T81 VGH/VGL probe setup (2026-08-11, board 2, `1531d1d`)

Board 2 left on a forced 8 °C (LUT 235, `! DEBUG 5s/REFRESH/LUT`): ~3.03 s of
sustained drive per refresh against ~1.93 s at 241, i.e. ~30 samples per drive at
the multimeter's 10 Hz ceiling, and the condition where a marginal charge pump
shows first; refresh every wake, ~8 s apart. Pads per
`hardware/thermometer-c6/README.md:52-59`: VGH = C2, VGL = C1 (4.7 µF / 25 V),
PREVGH = C5, PREVGL = C11 (boost outputs ahead of the panel's regulation). Not
deployment-safe.

### Power-capture baseline and sweep (2026-08-11, board 2)

Baseline `2f22620`, `thermometer_c6_release`, no flags. `-DPPK2_DEBUG` withdrawn:
no digital leads, so `ppk2_selftest()` (~40 ms per wake, 2×10 ms CPU + 5×4 ms
display) and the 3×50 ms D1 preamble on flush wakes would inflate a ~7.7 mC wake
by several percent; `ppk2.py`'s current-derived regions separate ≈18 µA / mA /
~100 mA+ without markers, at the cost that the ~0.04 mC journal append cannot be
separated from the refresh. `-DREFRESH_EVERY_N_WAKES=10 -DDISPLAY_TEMP_DELTA=99`
withdrawn: it caps quiet windows at ~10 min where board 1's 18.3 µA needed 2397 s,
and the floor is ~78% of the budget. `DISPLAY_TEMP_DELTA` gates only the refresh
decision (`src/Thermometer.cpp:2102`), not storage.

Sweep `ccfde51` (bounded: `tools/ppk2.py` stamped the host tree at 19:26Z, the
flash immediately preceded it), `-DBATTERY_SHUTDOWN_DISABLED -DDISABLE_WIFI`: 11
of 13 linear steps before a tool bug (`np.bool_` in `alive`, `notes.md`),
HEALTHY 4200 → 3400 mV, DEGRADED at 3300 and 3200; captures recovered with
`sweep --replay`; `summary.json` and `report.md` in
`local/sweeps/ppk2-sweep-20260811-192621/` carry
`status: replayed (no bisect — needs hardware)`. The cliff is a 3400-3300 mV
bracket; board 1's is 3317-3320 mV. The sweep power-cycles, so the archive is
not implicated.

### BOD probe under the T81 (2026-08-11, board 2, `2541adc-dirty`)

Result: at 4.23 V in, a T81 refresh pulls 3V3 below the ~3.27 V SEL_2 trip.

| Level | Behaviour |
|---|---|
| `CONFIG_ESP_BROWNOUT_DET_LVL_SEL_2` (~3.27 V) | boot loop at ~0.8 s: 30 boots, 30 `E BOD: Brownout detector was triggered` in 25 s, `Battery level: 4220-4236 mV`; 8 die on `Display dashboard (920x680)`, 22 on the line before, none in boot / LP / sensor / ADC / sleep |
| `SEL_3` (~3.10 V) | clean: 1 boot, 0 brownouts, renders 2434 / 1870 ms at 228 slices (LUT 241) |

Rail minimum during a refresh at 4.23 V is bracketed 3.10-3.27 V (IDF estimates,
adjacent levels). Board 1 needed VIN ≤ ~3.57 V (3.56-3.59) to cross SEL_2 with
the 200×200 panel: 660 mV of headroom eaten by the bigger panel. The mechanism
looks like load-step transient response, not dropout: board 1's 2026-07-30
captures showed identical boot transients either side of the edge and a flat
~10 mA churn at `bootloops=0`. The ~300 mV droop and the
3550 / 3500 mV thresholds must be re-derived for the T81. Stale-sdkconfig trap:
`sdkconfig.thermometer_c6_bod_probe` won over `sdkconfig.defaults.bod_probe`, so
the SEL_3 edit was ignored until the generated file was deleted (rule in
`.claude/rules/build.md`); check `ESP_BROWNOUT_DET_LVL` in
`.pio/build/<env>/config/sdkconfig.json`. ROM download mode ignores the raised
level, so USB reflash recovers a boot-looping board; recovery here was the
`thermometer_c6_debug` LUT-8 arm.

### Boards 3 and 4 first power (2026-08-12)

Result: both render; fleet render timing **229 ± 1 slices** (board 2 228, board
3 230 then 229, board 4 230), first render after reset ~500 ms long (2378-2434
ms vs 1808-1870 ms). Phase 0 DMM rail pass skipped (board 2 set the precedent;
shared reflow and X-ray). Board 4's U5 was flagged slightly rotated at the
2026-07-29 visual pass (`BRINGUP.md:57-66`); it reads
`BMP581 detected (chip ID 0x50)`, so the skew is benign. No 32k-XTAL fallback
warning on either. Board 3 logged `LP core temp: 31.28 °C`. Both wrote
`base seq 1`. Sensors 30.65 °C (board 4), 33.79 then 31.26 °C (board 3): USB
self-heat, not ambient. A panel-less board stalls in the BUSY wait and latches a
fault that needs a restart: fit the panel with power off. The PPK2 occupies two
`/dev/ttyACM*` nodes while sourcing, and two back-to-back uploads to one by-id
path race for the port.

### Soak start (2026-08-11/12)

Boards 3 and 4 (`753afbc`, erased): upload SUCCESS with esptool's hash check,
footer confirmed with no badges. A full boot → render → sleep cycle was not
proved (release has no serial; a dump wipes RTC); the substitute is the boot
counter past `#1` after ten minutes.

Board 2 (`11cd8dd`, erased 1.2 s, still on USB so the dump cost nothing):
`ESP_BROWNOUT_DET_LVL: 7` read from
`.pio/build/thermometer_c6_release/config/sdkconfig.json` (release did not
inherit the probe's SEL_3), baked `GIT_HASH` `11cd8dd` clean, no
`PLATFORMIO_BUILD_SRC_FLAGS` (`env -u`), `LP_CORE_IDLE` commented at
`ulp/lp_core_main.c:21`. Archive:
`base seq 1 written 2026-08-11 22:46:18Z cursor 0x000000`,
`formatted by 11cd8dd`, 0 / 1 / 0, identity `GDEH0576T81/BMP58x`; the timestamp
is real wall clock (~90 s after upload) against a header
`created (before first NTP sync)`, so NTP, the credentials and the static lease
are live. Soak t=0 = 2026-08-11 22:49Z, USB out, 400 mAh pack in; panel then
showed a ULP-woken refresh at 3998 mV (4004 mV on the first render, surface
charge). Boards 2 and 4 sit ~10 cm apart as the co-located pair; the erase
removed hundreds of brownout-edge boots from the BOD probe. Deferred for the
soak: the FPC-in/out floor pair (19.05 µA board 2 vs 18.3 µA board 1), which
needed ~2 h of settled windows on the PPK2 harness.

Board 3 (`52cf257`, erased, output not captured): panel at t=0 4188 mV,
`Aug 12 2026 18:27`; NTP synced at first boot (the new AP was reachable), so the
drift anchor is real; fourth render 4186 mV (2 mV step vs board 2's 6 mV), so
the pack is at ~4.19 V. Boards 2 and 4 run their packs as ordered, never charged
(~4000 mV on each board before charging, which bounds VBAT divider spread at
tens of mV); only board 3's pack was charged. Thresholds `low_battery_mv = 3550`
/ `no_battery_mv = 3500`: board 3 has 688 mV of span, the pair ~497 mV, so the
pair reaches cutoff first (an as-shipped cell near 4.00 V is ~three-quarters
charged, estimated). Board 3's DHCP term was deliberately not measured before
sealing. `! NOSYNC` at the bench was expected (destination AP absent).

### Published figures re-decoded (2026-08-23 harvests)

Arm 1 image: the 10 `arm`=0 records re-decode to +5066.3 ppm / ±4.5%; the
2026-08-05 harvest published +5066 ppm (+4839…+5247, ±4.5%) off a different
image, through a no-erase reflash and 18 days. Arm 3 image: the 3 pre-experiment
records re-decode to +304.5 ppm against a published +305. First `arm`=1 record
carries `d_boot = −658` (boot counter backwards across the RTC wipe; dropping it
moves the mean 1.4 ppm). Arm 3's first record ran 3.49 d against a 12 h setting
with `d_boot = −893` (no `erase_flash` at the arm flash, so `drift_state_load()`
restored the 3.47 d interval). 12 of 28 arm-3 resync attempts failed, read from
window lengths of 24 / 36 / 37 / 49 h, against `resync_fail_count == 0` at the
day-4 gate check on a 296x128 panel too small for the sync-age token.

Bench notes: `--baud 921600` fails a `--full` read on this CH340
(`Corrupt data, expected 0x1000 bytes but received 0xff0 bytes`); 460800
completed first time, although `history.py`'s default and help string still say
921600. Boards 1, 2 and 4 packs took ≲5 mAh (~1% of 400 mAh) while docked. Board
1 and arm 5 needed a manual park: the by-id node vanished ~2 s after the plug-in
wake. Board 1 is left parked in ROM download mode (retired); arm 5 was RST'd
back to running.

### Arm 2 crossover (2026-08-23, FireBeetle)

Pre-flash checks on `668ff6d`:
`ULP size check: UlpProgramBMP390L.cpp = 110/128 words` (the `ULP_ALWAYS_WAKE`
signature; 127/128 without), baked `GIT_HASH` clean, clean tree.
`build_src_flags` instead of the global `build_flags` the 2026-08-05 rows used:
every macro is read under `src/`, and `scripts/check_ulp_size.py` preprocesses
with `build_src_flags`. Panel `! EXP 2 60s/RESYNC/REFRESH`,
`! DRIFT +221s/12h +5085ppm n6 ±0%` (ring restored across the RTC wipe), but
`! NOWIFI` and `! NOSYNC x1`: the working copy held board 3's network list.
Reflashed `ef27bd0` after the fix; panel clean. Binary size is the only
discriminator git cannot give (966624 vs 966720 B, a 96 B delta of network
strings on an identical tracked tree); the hashes differed only because the
arm-1 write-up was committed in between. A flash that changes `local-secrets.h`
needs `! NOWIFI` / `! NOSYNC` checked on the first frame, and rows should name
which secrets were compiled in. `2fccb5f` escalates absent-network retries, so
bench time is expensive.

### Arm 4 LP pin (2026-08-23, `xiao-hat`, BUG)

`TEMP_DELTA_THRESHOLD_C 0.0f` cannot be a `-D` (the LP sub-build inherits no
flags), so it was edited into `ulp/lp_core_bmp58x.h` and committed (`49245c9`).
The header edit never reached the LP binary: `ulp_main.bin` md5 `bde10fbd3b03`,
identical to the unmodified `0.1f` build. The panel showed
`! EXP 4 60s/RESYNC/REFRESH` with the right hash and the upload verified. Root
cause in `.claude/rules/ulp.md`; upstream platform-espressif32 #517, open since
2021. Reflashed `cfcc35f` after `rm -rf .pio/build/<env> .pio/build_cache` with
the pin in `ulp/lp_core_main.c`: md5 `14d6e676a309`, distinct from vanilla, hash
clean, panel confirmed. Two manual parks were needed: esptool's closing
`Hard resetting via RTS pin` released the first park and the board booted,
rendered and slept (contrary to the 2026-07-30 finding that a park survives it).
Pin reverted on master in `250a53f`; the sensor programs were later inlined into
`lp_core_main.c` (`ce1e516`), so a re-pin goes there.

### Return to production (2026-09-16)

Arm 5 ended after 42 days (`2994f30`, no compensation on the C6), arm 4 after 24
(`bbc7bd7`, vanilla LP binary), arm 2 after 24 (`fe3f7cb` then `68af393`, which
refits the restored ring so the correction arms at first boot). The first drift
record after each flash straddles the 12 h interval and is to be discarded.
Expected panels: fresh frame, the new hash, no `! EXP`. FireBeetle confirmed:
footer `c+4820` right after `lp0`, `! DRIFT +210s/12h +4799ppm n6 +-1%` (the
restored arm-2 record, clears at the first resync); the level is the
recency-weighted fit of the six restored rates. `tools/driftstats.py` re-decodes
the arm 0 / 1 subsets to +5066.3 / +5124.6 ppm, arm 3 to +607.2 ppm, and the 32
August arm-5 records to +877.9 ppm.
