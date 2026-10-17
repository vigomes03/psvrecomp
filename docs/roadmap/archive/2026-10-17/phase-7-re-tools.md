# Phase 7: RE and Debug Tools (continuous, since phase 1)

**Audit (2026-10-17):** tools are partly present, not the whole study workflow.
`runtime/fnprof.c` and `recomp/sym.py` exist; 7.1's action diff and 7.2's full symbol/disassembly path need validation.
7.3 memory search/poke remains unverified. 7.4: `tools/verify/run_auto.sh` collects frames; the named LAS script suite
was not found in the inspected `psvrecomp/` tree. 7.5: hooks are listed in `psvrecomp/README.md`; coverage remains open.
Crash reporting is recorded in the pipeline log (2026-10-16); the old "missing crash log" note below is superseded,
while the interactive error box still requires a manual test.
7.6/7.7: the generic REA harness exists; game-sized snapshots and reviewed game findings remain unverified.
7.8/7.9: naming database and Ghidra bridge remain open. No `docs/re/` directory was found in this audit.

**Objective:** see inside the game. LAS did RE **instrumenting the recompiled game**; we added REA/Ghidra.

## From LAS (port)
- [ ] 7.1 🤖 `FN_ENTER` + `PVR_FNPROF=<from>:<to>`: function entry count between frames; **diff between two
  executions** shows which code an action activates.
- [ ] 7.2 🤖 `sym.py`: address → module+offset → symbol (if any) + disassembly (Capstone).
- [ ] 7.3 🤖 Memory value search/"poke" (`ADDF_MATCH` from LAS) to find structures (player position, camera, HP).
- [ ] 7.4 🤖 `shot.sh`/`frames.sh`/`montage.sh` + image metrics (`transients.py`, `bandmetric.py`).
- [ ] 7.5 🤖 Documented `PVR_*` hooks where they are defined (scripted input, temporary save, screenshot at frame N...).

## Historical status as of 10/15 (crash-report follow-up in audit above)
- 🟢 Diagnostic kit by `PVR_*` variables (list in `psvrecomp/README.md`), `tools/rea/glsl_slice.py`,
  `tools/verify/run_auto.sh`, gates.
- Historical gap, no longer wholly missing: **crash log/warning:** the game closes without a message. Item: error box with the cause (`FATAL`) and the log
  copied with date, plus a summary of the last state (scene, frame, last `[draw]`/`[svc]`).

## Ours (REA)
- [ ] 7.6 🧠 Convert each NSO to analyzable ELF (or Ghidra NSO loader) and create **REA snapshots** by build id
  (`lab/snapshots`, ignored).
- [ ] 7.7 🤖 `rea_worker` with questions about the Pokémon: "who calls X", "what does function Y do", with contract and review.
  Findings go to `docs/re/` (description, not code).
- [ ] 7.8 🧠 Names: name base for discovered functions/structs (`work/names.tsv`: address, name, evidence),
  consumed by `sym.py` and Ghidra.
- [ ] 7.9 🧠 "Ghidra ↔ recompiled" bridge: open in Ghidra the function that `fnprof` pointed to; in the generated code,
  comment with the discovered name.
