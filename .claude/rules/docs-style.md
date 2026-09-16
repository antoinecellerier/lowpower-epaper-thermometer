---
paths:
  - "docs/*.md"
  - "docs/**/*.md"
  - "readme.md"
  - "hardware/**/*.md"
---

# Logbook and research-doc style

Written for a human scanning for a number and its conditions. Data is
append-only; prose around unchanged data may be restructured freely.

## Shape of an entry

1. Heading is a neutral label: what, where, when.
   Yes: `### Arm 5 harvest, 2026-08-23`. No: `### Arm 5 kills the duty-cycle reading`.
2. First sentence is the result.
3. Conditions line: rig, env, build hash, build flags, supply node, ambient.
4. Numbers in a table. Each figure carries n, window and a source a reader can
   open (capture file, log line, photo path, commit). One bold per table, on
   the headline figure. "unmeasured" is a valid cell value.
5. At most one short paragraph of interpretation, then an `Open:` list of what
   the entry leaves unmeasured.

Budget: a capture or harvest section is under ~40 lines including tables. A
validation-log row is 3-5 lines. Longer means a second entry or a table.

A logbook that opens with a Results table updates the row whenever a later
entry supersedes the figure to quote; the row links to that entry.

## Prose

- One fact per sentence. No nested asides, no dashes as parentheses.
- State what was tested, seen and concluded. Do not narrate the reasoning path.
  Yes: "Board 4 shows no wake-rate trend, so board 2's slope is noise."
  No: "This is the cheapest kill of a duty-cycle reading this project has
  managed, and it cost no extra hardware."
- A killed hypothesis gets one sentence: hypothesis, evidence, verdict.
- Facts, not observers: `Panel: c+4820`, not "the operator read the panel".
- Bold marks the headline figure, never a sentence. Tables: plain text in
  setup and condition cells, bold only on the measured headline figure
  (`readme.md` power table: bold only the `@4V2 bat` figures). Do not infer
  formatting from neighbouring entries; this file is the spec.
- Superseded planning text is replaced by a gate / expected / observed / date
  table, not kept alongside the outcome.
- Bench-operation lessons (port naming, tool flags, tool bugs) go to the
  `/device-session` skill or the tool's own docs. The log gets a pointer at most.
- Numbers follow CLAUDE.md "Numbers are measured, not guessed": source, date
  and conditions travel with every figure.
- Wrap prose at 80 columns. Never split a link or a code span across lines.
  `tools/docs/docwrap.py check FILE` reports overflow, ragged paragraphs and split
  spans; `fix` reflows them, whitespace only. `tools/docs/docstats.py -b REV FILE`
  shows what a rewrite changed in size, sentence length, asides and long cells.

## Restructuring a logbook

Prose may be rewritten around unchanged data. Gate it with `tools/docs/docinv.py`:

- `diff OLD NEW`: every token missing from the new file is restored, or listed
  with a reason for the user to veto.
- `diff NEW OLD`: every token new to the file traces to an old sentence
  (a rounding, a heading label), or goes.
- Keep every hedge: derived stays derived, superseded stays superseded, two
  runs' ranges do not merge into one. A second reader checks old against new
  before the commit; these were the failures found so far.

## Which file

| File | Holds |
|---|---|
| `notes.md` | power: PPK2 captures, budgets, sleep floors |
| `clock-drift.md` | RTC drift rates per board, compensation |
| `history-store-validation.md` | flash archive results on hardware, and every flash / erase / inject as a device-state row |
| `footprint.md` | binary size and build time, one row per significant change |
| `captures/`, `photos/` | every PPK2 screenshot and photo; cite by relative path so the link opens |
| `README.md` | index, one row per doc with a status; a new doc adds its row |
| `archive/` | finished or abandoned work, moved here with a banner stating the outcome; never deleted |
| `hardware/thermometer-c6/README.md` | board reference; opens with the doc table (one row per doc with a status), a new doc adds its row |
| `hardware/thermometer-c6/BRINGUP.md` | the live bench queue and per-board state; a closed phase moves to `thermometer-c6/archive/` |
| `hardware/thermometer-c6/archive/` | routing snapshots, orders, closed bring-up phases; an order directory describes boards that exist and is append-only |
| `hardware/datasheets/` | vendor PDFs for every panel and carrier, and the panel readback findings |

`readme.md` gets a one-line pointer to the logbook, never the finding.
A hardware doc carries board state and links the logbook entry that holds the
measured figure; it does not restate the figure.
