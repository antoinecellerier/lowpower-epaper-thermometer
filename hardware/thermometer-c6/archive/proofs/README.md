# Part geometry proofs

Each directory proves one footprint, orientation or datum claim from primary
sources: the STEP model, the vendor drawing, and an annotated render or overlay.
`VERDICT.md` in each directory states the claim and the result first. The
generator, `verify/` and the board docs cite these paths as their evidence.

The four rev A proofs were moved here from the untracked `out/` on 2026-10-27.
Their internal paths were rewritten to match. The prose is otherwise as written.
How to write a new proof: the `pcb-edit` skill, "Proving a part's geometry".

| Proof | Date | Claim tested | Verdict | Fix | Key images |
|---|---|---|---|---|---|
| [`j4-proof/`](j4-proof/VERDICT.md) | 2026-07-19 | J4 FPC tails vs mouth | mouth faced west into the board; rotate 180 | `77c3ebd` | `proof_step_render.png`, `proof_board.png` |
| [`j3-proof/`](j3-proof/VERDICT.md) | 2026-07-19 | J3 USB-C pads vs part | mouth faced south; the 3D model was seated 180° off the copper | `e22be63` | `proof_overlay.png`, `proof_pads.png` |
| [`j3-proof/MODEL-SEATING.md`](j3-proof/MODEL-SEATING.md) | 2026-07-20 | J3 3D model offset after the flip | pegs, posts and tails register | `26cebbc` | `seating_before.png`, `seating_after.png` |
| [`j3-datum/`](j3-datum/VERDICT.md) | 2026-07-20 | HRO "5.79" datum | J3 sat 1.415mm too far north | `aae8b6c` | `datum-proof.png`, `side-by-side.png` |
| [`j3-land/`](j3-land/VERDICT.md) | 2026-07-20 | J3 land vs measured solder foot | heel +0.080, below IPC Least; shift the row 0.170 | `aae8b6c` | `land-proof.png` |

`j4-proof/` quotes a 6.55mm tail-to-mouth depth. `j3-land/` §7 replaced it
with 4.95mm (body 5.40). The orientation verdict is unaffected.

## Rerunning

Run the scripts from `hardware/thermometer-c6/`. Two inputs are untracked:

- STEP models in `local.3dmodels/`, fetched by `fetch-3dmodels.sh`.
- `datasheets/HRO_TYPE-C-31-M-12_datasheet.pdf`, the URL in the J3
  footprint's `descr`. `j3-datum/vector.json` is its parsed vector content,
  so most `j3-datum/` and `j3-land/` scripts run without it.
