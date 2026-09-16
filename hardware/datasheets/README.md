# Datasheets and vendor schematics

Vendor PDFs for every panel and carrier board a rig uses. They live here
rather than under `../thermometer-c6/` because the panels and carriers are
shared across every rig — FireBeetle, XIAO, the Seeed hat and the custom
board. That board keeps its own parts' datasheets beside it, but **untracked**
— including the SSD1677 doc referenced below, which is not in the repo and has
to be fetched again from Solomon Systech.

## Carrier boards

| File | What | Rig |
|---|---|---|
| [`DESPI-C02 Connector Board for E-paper Display V1.1.pdf`](DESPI-C02%20Connector%20Board%20for%20E-paper%20Display%20V1.1.pdf) | Good Display DESPI-C02 adapter spec | the DESPI-C02 rigs (`firebeetle`, `xiao-bigscreen`) |
| [`DESPI-C02_SCH V1.0.pdf`](DESPI-C02_SCH%20V1.0.pdf) | DESPI-C02 schematic; transcribed in [`../thermometer-c6/README.md`](../thermometer-c6/README.md) | same |
| [`Seeed ePaper Driver Board for XIAO SCH v1.0.pdf`](Seeed%20ePaper%20Driver%20Board%20for%20XIAO%20SCH%20v1.0.pdf) | Seeed XIAO ePaper driver board schematic | `xiao-hat` |
| [`XIAO ESP32-C6 v1.0 SCH.pdf`](XIAO%20ESP32-C6%20v1.0%20SCH.pdf) | Seeed XIAO ESP32-C6 schematic | every XIAO rig |

## Panels

| File | Panel | Controller | Rig |
|---|---|---|---|
| [`GDEH0154Z90.pdf`](GDEH0154Z90.pdf) | 200x200 tri-colour | SSD1681 | `firebeetle` |
| [`GDEY0213M21.pdf`](GDEY0213M21.pdf) | 212x104 (as GDEW0213M21) | UC8151D | `revA-213m21` bench spare |
| [`GDEW029I6FD.pdf`](GDEW029I6FD.pdf) | 296x128 flexible | UC8151D | `xiao-hat` |
| [`GDEH0576T81.pdf`](GDEH0576T81.pdf) | 920x680 | SSD2677 | `revA-bigscreen`, `xiao-bigscreen` |
| [`UC8151D.pdf`](UC8151D.pdf) | — | UC8151D chip-level | the two UC8151 panels above |

No chip-level SSD2677 doc. The SSD1677 datasheet is a relative, not the part;
taking its chip pinout as the module's cost a wrong conclusion once (below).

## What they settle: panel readback

Whether a panel can answer the host is a property of its **controller**, not of
any board, so there is no single answer. Every one of these modules exposes a
single serial data pin and no SDO: M21 and I6FD call it `SDIN`, the Z90 and T81
call it `SDA`. Readback, where it happens, is the controller driving that same
pin back (established 2026-08-05).

| Controller | Module data pin | Readback | Identifier | Source |
|---|---|---|---|---|
| UC8151D | `SDIN`, single | **measured working**: only three registers answer (REV, FLG, temperature); TRES and PSR float, as do foreign SSD168x commands (table below) | `0x70` REV → `LUT_REV` from OTP `0x001`, the one panel-intrinsic value on offer, since a waveform LUT is tuned to its glass | board 2 + GDEY0213M21, 2026-08-05 |
| SSD1681 | `SDA`, single; 4-wire read procedure documented | expected working, unmeasured | **`0x38`: 10-byte User ID in OTP**; the only thing that tells the Z90 from the GDEM0154I61 (behind the GDEY0154D67 driver), both on this controller | datasheet |
| SSD2677 | `SDA`, single, bonded to FPC pin 14 | **returns 0 over hardware SPI**; panel capability untested | unknown | board 2 + T81, 2026-08-11 |

UC8151D registers probed, board 2 + GDEY0213M21, 2026-08-05. Each answering
byte was identical whether the input was pulled up or down, so the line is
actively driven, and identical before and after GxEPD2's init.

| Command | Answer | Note |
|---|---|---|
| `0x70` REV | `01 0e` | driven |
| `0x71` FLG | `13 13` | driven |
| `0x40` temperature | `d2 00` | driven |
| `0x61` TRES | floats | before init too |
| `0x00` PSR | floats | before init too |
| foreign SSD168x commands | float | the control |

The T81's 0 is a verdict on the host, not on the panel: GxEPD2's `_readData()`
samples the data line from software and is documented to work only in
bit-banged mode, and this build runs hardware SPI, so nothing samples the line.
The 0 was measured indirectly: `_Init_Full` selected the ≤5 °C waveform on a
~26 °C panel, which is the `temp == 0` path and no other. An earlier version of
this table called the T81 doubtful because the FPC carries no SDO; `SSD1677.pdf`
names `SDI`/`SDO` as separate **chip** pins in 4-wire mode, but the module bonds
a single `SDA` to FPC pin 14 like the other three, so the T81 stands where the
M21 stood before its probe (one data pin, a module datasheet that calls it an
input and documents no read), and the M21 answered. Untested, not unlikely.
On the UC8151, resolution cannot be read back (TRES floats, and the datasheet
calls it a host-set override); resolution would in any case only falsify a
match, never confirm one, since both 200x200 panels agree on it. Nothing
depends on a T81 read any more, which is why the SSD2677 row stops short of a
board-level conclusion: the waveform consequence is fixed twice over in
firmware, upstream guards the failed read with a 20–30 °C default
(−48.4 % of panel busy time,
[`docs/notes.md`](../../docs/notes.md#t81-waveform-lut-selection-under-hardware-spi-rev-a-board-2-2026-08-11)),
and feeding the BMP581 reading in is strictly better than any readback:
calibrated, ambient rather than a self-heating die, and write-only, so it needs
no SPI-mode juggling.

Open:

- SSD2677 readback, probed in a mode that samples the line. What it buys is a
  cross-check of the controller's own sensor and an SSD2677 row here that says
  something: diagnostics now, not a fix, and never a board change
  ([`REV-B.md`](../thermometer-c6/REV-B.md#panel-readback-sdo)).
- SSD1681 `0x38` User ID on the Z90 and the GDEM0154I61: expected, unmeasured.

## Caveats before trusting any of this

- **Module docs understate it.** GDEW0213M21 Table 3-1 lists only `SDIN` and
  documents write procedures only, yet the panel demonstrably reads back. The
  capability is the chip's; the module vendor does not promise it, so it could
  vary between batches.
- **Nothing transfers between families.** An SSD168x command set floats entirely
  on a UC8151 and vice versa — measured both ways. Every family needs its own
  probe table.
- **These PDFs carry a diagonal "GOOD DISPLAY" watermark** that text extraction
  interleaves into the tables as stray `OD`/`AY`/`PL`/`IS`/`D`/`G` tokens. It
  reads convincingly as a column — it briefly looked like an open-drain pin type
  on the T81's `SDA`. Check any pin attribute against the rendered page.
- **The UC8151 framing is unresolved.** Reads give a stable `0x70` → `01 0e`,
  but the datasheet's `CHIP_REV` is `1101b`, and it notes OTP reads return a
  dummy first packet; bit alignment is the other candidate explanation. Usable
  as an opaque fingerprint; not as "the revision".

Firmware probe: `display_probe_readback()` in `src/Display.cpp`, behind
`EPD_PROBE`. It reads every command twice, against a pulldown and a pullup — a
floating line follows its pull, a driven one does not, so each run carries its
own control.
