# Build system

The tree is a standard ESP-IDF CMake project (`CMakeLists.txt` +
`src/CMakeLists.txt` + `components/`) that PlatformIO drives. Both boards build
`framework = espidf` on the official registry platform (`espressif32 @ ^7.0.1`,
ESP-IDF 6.0.1): no Arduino framework, no platform fork, no pinned zip URL.
`idf.py -DIDF_TARGET=esp32c6 build` also works: fonts and the GIT_HASH stamp
auto-generate at cmake configure time, so outside PlatformIO the stamp is as of
the last configure rather than the last build.

CLAUDE.md keeps only the rules that destroy data or silently mis-build when
violated. Everything here is the *why* behind them, plus the traps.

## libc is pinned to newlib

`CONFIG_LIBC_NEWLIB` is set deliberately. PlatformIO's `ulp.py` doesn't forward
`ADD_PICOLIBC_SPECS` to the LP-core sub-build, so IDF 6's picolibc default breaks
it. Revisit picolibc (~20% smaller binaries) when that's fixed upstream, or when
building exclusively with `idf.py`.

## Board macros

The macro names are Arduino-era leftovers, kept only to avoid churning every
`#if` in the tree; nothing Arduino remains. Where they come from is a rule, in
[`.claude/rules/build.md`](../.claude/rules/build.md).

## Vendored components

`components/gxepd2` and `components/adafruit_gfx` compile against
`components/arduino_shim`, a minimal Arduino API over IDF (GPIO, timing,
Print/Serial, SPIClass on spi_master).

Only the panels a rig header can select are compiled. **Add the panel
`.cpp` to `components/gxepd2/CMakeLists.txt` when enabling a new `USE_*` panel**,
or the link fails with a missing vtable rather than anything that names the panel.

`components/gxepd2/upstream` tracks
[`antoinecellerier/GxEPD2`](https://github.com/antoinecellerier/GxEPD2) branch
`t81-set-lut-temperature`: **stock upstream plus one additive commit** adding
`setTemperature()` to the T81 driver, so the host can choose the waveform LUT
instead of the driver reading a controller temperature it cannot get over
hardware SPI (`docs/notes.md`, 2026-08-11). Nothing else diverges: the 2026-08-11
migration that retired the old three-commit fork stands, and this rebases onto
any future upstream. **To build against stock upstream instead**, check the
submodule out at `origin/master` and pass `-DDISABLE_PANEL_LUT_TEMPERATURE`;
`display_set_lut_temperature()` then compiles to nothing and the panel keeps the
driver's fixed 20..30 °C fallback (verified 2026-08-11).

`components/hulp` (the ESP32-E ULP FSM library) registers empty on other targets.

## sdkconfig

Authored `sdkconfig.defaults` and `sdkconfig.defaults.<target>` are tracked;
generated `sdkconfig.<env>` files are gitignored. CPU is fixed at 80 MHz at build
time.

Worked example of why the authored/generated distinction matters (the rule is in
[`.claude/rules/build.md`](../.claude/rules/build.md)): `CONFIG_RTC_CLK_CAL_CYCLES=3000` on `thermometer_c6`
looks like a tuning decision, but it is the IDF default that follows from
selecting `EXT_CRYS`. Nobody here chose 3000.

A stale generated file bit a brownout-level change on 2026-08-11: the reflash
reported SUCCESS and the board kept the level being changed away from, because
the edited `sdkconfig.defaults.thermometer_c6` was never re-read. Delete
`sdkconfig.<env>` and verify the value in the built `sdkconfig.json`, as the
rule says.

## Partition table

Lives in `partitions.csv` (2048KB single app, no OTA; 1920KB `history` data
partition) and is referenced from BOTH `board_build.partitions` (PlatformIO
ignores the sdkconfig partition selection and always generates from this option)
and `CONFIG_PARTITION_TABLE_CUSTOM_FILENAME` (idf.py). Keep them pointing at the
same file.

`history` is at a fixed offset (0x10000) and must stay there. It comes before
`factory` so a future resize grows it upward and leaves written archive content
in place; moving its start orphans years of data. Changing the table relocates the
app, so that one upload must not be interrupted.

## Local artifacts

Everything the tools pull off a device lives under a single gitignored `local/`:

| Directory | Written by | Contents |
|---|---|---|
| `local/sweeps/` | `ppk2.py sweep` | one dir per run: raw captures, `report.md`, `summary.json` |
| `local/archives/` | `history.py backup` | `hist-<board>-<mac>-<date>.bin` partition images |
| `local/captures/` | `ppk2.py live --out/--raw-out`, Power Profiler exports | `ppk-*.csv`, raw bins; archive with `zstd -19 --long`, `ppk2.py` reads `.zst` directly |
| `local/scratch/` | by hand | ad-hoc bench files |

`tools/artifacts.py` resolves the root from the repo, **not from the CWD**, so an
artifact lands in the same place wherever the tool was launched from. Point
`$THERMO_LOCAL_DIR` at another disk when a sweep won't fit: a full one is a few
hundred MB, and `ppk2.py` refuses to start when the target filesystem is short.

Sweeps and captures are **cited from the logbooks by relative path**, so pruning
one breaks a doc reference. Check before deleting. Prefer dropping a run's
`*.bin` + `.dec*` caches to deleting the directory: `report.md` and the `*.json`
sidecars carry every conclusion at 0.05% of the size. `history.py backup -o`
takes whatever path you type, so `hist-*.bin` stays in `.gitignore` as a safety
net.

## Header naming

**Never name a project header like an IDF-internal one.** IDF's mbedtls exposes a
private `common.h` that shadowed ours, which is why ours is `app_common.h`.

## Generated fonts

`include/generated/` is auto-generated by the font scripts and gitignored. Don't
edit it, and don't reference specific files under it from documentation.

## ULP builds

PlatformIO's espidf builder feeds **every** file in `ulp/` to the active ULP
toolchain. That is why `ulp/lp_core_main.c` is wrapped in `#ifdef __riscv`: on
ESP32-E the FSM pass preprocesses it to nothing, and HULP builds the FSM program
at runtime instead.

The ULP FSM word budget is checked at build time. `scripts/check_ulp_size.py`
preprocesses the program arrays with the real toolchain and fails the build past
`CONFIG_ULP_COPROC_RESERVE_MEM/4` = 128 words (currently 127/128). The runtime
loader also logs the count and degrades to safety-net wakes instead of aborting
if it ever misfits.

On ESP32-E, `CONFIG_ULP_COPROC_RESERVE_MEM=512` preserves the layout
`ULP_DATA_BASE` assumes.

### Stale LP binary after a header edit, 2026-08-23

PlatformIO signs the LP object on `lp_core_main.c`'s own content. When the
sensor programs were headers under `ulp/`, editing one rebuilt nothing and the
previous `ulp_main.bin` was embedded again, silently, with a successful build.
An `#error` in `lp_core_bmp58x.h` did not fail the build; the same `#error` in
`lp_core_main.c` did. Neither touching the source (the decider is content, not
mtime) nor deleting `esp-idf/src/ulp_main/` helped, since nothing left in the
graph needed the artifact. A generated stamp file in `ulp_sources` did not help
either: the stamp recompiles, the stale object is `lp_core_main.c`'s. Only a
build with `.pio/build_cache` cleared produced a correct binary.

The cause is upstream and long-standing:
[platform-espressif32 #517](https://github.com/platformio/platform-espressif32/issues/517),
open since March 2021, reported there as ULP sources going unnoticed. What it
cost here: an experiment arm was flashed with the wrong wake cadence while the
`! EXP` badge, the ULP word-count check and the baked git hash all reported
success. The rule that follows (no headers under `ulp/`, verify the binary's md5
after a cache clear) is in [`.claude/rules/ulp.md`](../.claude/rules/ulp.md).

## platformio.ini structure

Why base sections are plain sections rather than `[env:...]` is a rule, in
[`.claude/rules/build.md`](../.claude/rules/build.md). The consequence worth knowing separately: `build_flags`
is not inherited through `extends` the way you would expect, so each env
re-states its own. The comments in `platformio.ini` track which flags that
affects.

## PLATFORMIO_BUILD_FLAGS is part of the project checksum

`.pio/build/project.checksum` covers the environment variable too, not just
`platformio.ini`. Changing `PLATFORMIO_BUILD_FLAGS` between invocations
therefore invalidates the whole tree and PlatformIO **deletes every env's
`.pio/build/<env>` directory**, not only the one being built.

So a finished image does not survive building another env with different flags:

```bash
PLATFORMIO_BUILD_FLAGS="-DPPK2_DEBUG" pio run -e seeed_xiao_esp32c6_epaper_release
pio run -e dfrobot_firebeetle2_esp32e_debug   # <- wipes the C6 image just built
```

This bites hardest between building a measurement image and flashing it: the
artifacts vanish with no error, and the flash then fails on missing files. Pass
the same flags to every env in a batch, or finish the flash before building
anything else.

`build_cache_dir` (see `[platformio]`) makes recovery from a wipe cheap but does
not prevent it. Measured on `dfrobot_firebeetle2_esp32e_debug`: rebuilding a
deleted env directory drops from 110s to 47s with zero recompiles; the remainder
is the cmake reconfigure and copying the objects back.

`scripts/prune_build_cache.py` bounds that cache, since SCons never evicts and
every build pushes a fresh ~11MB `firmware.elf`:

- Entries unused for 30 days are removed. Age is a true LRU because SCons
  `utime()`s an entry whenever it retrieves one.
- A stamp file gates the walk to at most weekly: 3.7µs on a gated build, ~50ms
  for a real pass over 12k entries.
- Only files inside the 2-hex-char shard directories are touched, so the
  SConsign DB and `config` at the cache root are never deleted. Deleting the
  SConsign would cost every env its build state.

`PLATFORMIO_BUILD_SRC_FLAGS` is the better tool for a bench flag that only
`src/` reads, because it keeps the framework objects out of the rebuild. It
trips the same checksum, so it does not avoid the wipe.

## Environments

Each carries a `custom_rig` naming the hardware it is built for, so the env is
the whole selection:

```
env                                            rig              board
dfrobot_firebeetle2_esp32e_debug / _release    firebeetle       ESP32-E (default env)
seeed_xiao_esp32c6_debug / _release            xiao-bigscreen   XIAO C6 + DESPI-C02
seeed_xiao_esp32c6_epaper_debug / _release     xiao-hat         XIAO C6 + Seeed ePaper board
thermometer_c6_debug / _release                revA-bigscreen   custom rev A board
thermometer_c6_bod_probe                       revA-bigscreen   rev A bench probe: brownout
                                                                raised to ~3.27V — never deploy
```

The rev A boards differ only by panel, so they share these envs and the default
suits boards 2-4. **Board 1 wears the 200x200 GDEY and needs
`RIG=revA-smallscreen`**. This is the one mismatch the rig cross-checks cannot
catch, since both rigs are valid for the env.

`scripts/upload_gate.py` closes it at upload time instead. HistoryStore stamps the
panel it was built for into the `history` partition header, and that partition
survives reflashing, so the gate reads 52 bytes back before writing anything and
refuses to flash a rig whose panel disagrees with what the board last ran. Only
the panel is checked: a wrong sensor or board macro still renders a frame and the
firmware badges it, whereas a wrong panel fails silently because the panel is
what breaks.

It skips itself, out loud, whenever the answer is not decisive (no archive yet,
unreadable header, no port), because a gate that blocks correct uploads gets
switched off. Overrides: `ALLOW_RIG_CHANGE=1` for a deliberate panel swap,
`SKIP_BOARD_CHECK=1` to skip the read entirely. Costs one esptool connect, which
resets the chip; the upload that follows would have anyway.

Testable with no board attached: it decodes a saved archive image and runs every
rig against it:

```bash
python3 scripts/upload_gate.py local/archives/hist-xiao_esp32c6-fffe16-2026-08-05.bin
```

## Rig selection

A rig is one hardware configuration: board + panel + sensor + the flags that
follow (`EPD_POWER_GATE`, `DISABLE_LEDS`). Each lives in a tracked
`include/rigs/<name>.h`; `include/rigs/_template.h` lists the options and the
add-a-rig checklist.

`scripts/pre_build.py` resolves `RIG` from the environment, else the env's
`custom_rig`, and writes `include/generated/rig_config.h`, a fixed-path,
two-line selector. Fixed on purpose: switching rigs changes that file's
*content*, not the project's file list, so the project checksum is undisturbed
and another env's finished `firmware.bin` survives. Varying
`PLATFORMIO_BUILD_FLAGS` instead would delete every env's build directory (see
above), and the LP core would not see the change at all: its sub-build
inherits no `build_flags` and reads the selector by relative include.

`include/generated/git_hash.h` exists for the same reason. As a `-D` on the
global SCons environment the commit hash reached every ESP-IDF component's
compile line, and SCons puts defines in the build signature. Every commit and
every clean/dirty flip (the first edit after a commit, and the revert after it)
recompiled ~1100 framework objects. As a header only the three sources that read
it rebuild.
`include/git_hash.h` wraps it so `tools/sim` and `tools/hstest`, which pass
their own `-DGIT_HASH`, keep winning.

Each rig header ends in a cross-check that `#error`s when the rig and the env
disagree, so `RIG=firebeetle pio run -e seeed_xiao_esp32c6_debug` fails at
compile time rather than at the panel. `idf.py` needs `-DRIG=<name>` once; the
generated header persists for later bare `idf.py build` runs.
