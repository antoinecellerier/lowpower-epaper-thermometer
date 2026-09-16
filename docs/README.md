# Docs index

Logbooks hold measured data and are the authority for any figure quoted
elsewhere; read the entry before quoting a number, and carry its date and
conditions. Style for everything here: `.claude/rules/docs-style.md`.

| Doc | What it is | Status |
|---|---|---|
| [notes.md](notes.md) | Power logbook: PPK2 captures, sleep floors, refresh and resync charge, daily budgets per rig, open items | logbook |
| [clock-drift.md](clock-drift.md) | RTC drift rate per board and clock source, phase 1-2 runs, compensation | logbook |
| [history-store-validation.md](history-store-validation.md) | Flash archive proven on hardware; every flash, erase and inject as a device-state row | logbook |
| [footprint.md](footprint.md) | Binary size, RAM, RTC and build-time ledger, one row per significant change | logbook |
| [wiring.md](wiring.md) | Prototype wiring tables per rig, DESPI-C02 power gate, Seeed ePaper board compatibility | reference |
| [build-system.md](build-system.md) | Why the build is shaped as it is: libc, components, sdkconfig, partitions, envs, rig selection | reference |
| [display-design.md](display-design.md) | Layout zones per panel size, footer fields, renderer architecture, RTC memory budget | reference |
| [wifi-provisioning.md](wifi-provisioning.md) | Design for moving WiFi credentials into NVS, 2026-08-10 | proposal, not implemented |
| [sim-fidelity-todo.md](sim-fidelity-todo.md) | Gaps between `tools/sim` and the device renderer | open items |
| [captures/](captures/) | PPK2 screenshots cited from `notes.md` | evidence |
| [photos/](photos/) | Prototype and rev A board photos | evidence |
| [../hardware/datasheets/](../hardware/datasheets/README.md) | Panel and carrier vendor PDFs, panel readback findings | reference |

## Archive

Finished or abandoned work, kept as a record. Each file opens with a banner
stating the outcome; nothing in `archive/` describes the firmware as it runs today.

| Doc | What it was | Outcome |
|---|---|---|
| [archive/ulp-plan.md](archive/ulp-plan.md) | ULP power optimisation plan, 2026-03 | implemented, by a different I2C path than planned |
| [archive/rtc-i2c-research.md](archive/rtc-i2c-research.md) | ESP32 RTC I2C controller and ULP instruction research | hardware RTC I2C abandoned for HULP bit-bang |
| [archive/esp32c6-lp-core-research.md](archive/esp32c6-lp-core-research.md) | C6 LP core research, Arduino era | LP core shipped; build path replaced by the ESP-IDF migration |
| [archive/multi-device-research.md](archive/multi-device-research.md) | Protocol comparison for multiple sensor nodes | research only, never implemented |
| [archive/shelved-features.md](archive/shelved-features.md) | `feature/dpp-provisioning` branch, Wi-Fi Easy Connect | shelved with the platform fork |
| [archive/org-review-2026-07.md](archive/org-review-2026-07.md) | Config and code organisation review, 2026-07-06 | actionable items applied same week; snapshot not maintained |
