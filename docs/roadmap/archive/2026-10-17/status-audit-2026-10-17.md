# Roadmap evidence audit — 2026-10-17

## Scope and interpretation

Documentation audit of phases 0-10 against the current roadmap, `docs/pipeline-log.md`, the machine-generated
`work/evidence/gates.jsonl`, and targeted source inspection. No game, build or RE experiment was rerun here.
This is a status reconciliation, not implementation work or a certification of the current binaries.

- **Gate-backed (historical):** the recorded checks support the stated narrow result for that run/build.
- **Observed / partial:** source, a recorded manual test or run_auto observation exists; the entire task's
  acceptance criteria are not established. Keep the parent checkbox open.
- **Pending / unverified:** no adequate evidence located in this audit; this does not prove no code exists.
- **Deferred:** a prior explicit user decision; do not silently turn it into resolved or mandatory work.
- Proposed priorities below are recommendations, not new user-approved deferrals.

The dated audit at the top of each phase is authoritative over historical investigation notes below it.
Checked historical tasks do not establish exhaustive instruction, service or gameplay coverage.
Do not compute an overall completion percentage from these unequal, composite tasks.

## Evidence register and limitations

| Evidence | What it supports | What it does not support |
|---|---|---|
| run_id=131ff828b2, dumps | Pinned v4.0.0 exefs files and 30-file nonempty romfs under `dumps/v400/` | Full cryptographic integrity of all assets; the base dump; the proposed `dumps/update/` path |
| run_id=990a33212b, boot | DLL loading, 227,207 functions reported, reaches init_sdk | Clean boot: it records exception c0000005 at 0x20; not the claimed 271,027-function count |
| run_id=7adc0390c2, boot | v4.0.0 reaches frame markers and time limit in six recorded attempts, 233,121 functions | Standalone synchronization stress/FIFO correctness or current build health |
| run_id=db35401e31, boot | Base reaches frame markers and time limit in four recorded attempts | Whole-game stability |
| run_id=312d34de1a, window | New-game scripted scene changes, rendered screenshots, measured frame rate | Semantic recognition of logo/title/control; controller hardware; pixel-perfect parity |
| run_id=c6a80b10d8, window | 600 seconds from copied open-world save, 17,227 frames, final windows 28.9 fps | Random exploration, all regions, current-build regression coverage |
| run_id=782956f97a, simd | 20,000 encodings / 159,968 semantic cases, zero reported failures; separate validity census | Exhaustive semantics for every valid encoding; integer instruction corpus in 1.4 |
| run_id=6efc28c218, excl_pair | Five codegen checks and 200 Unicorn semantic cases | Broad recompiler or concurrent-memory correctness |
| run_id=648a2fa61b, host | Recorded build failure at audio.c:943: undeclared SDL_GetCurrentAudioDriver | Evidence that a later current build passes; evidence that the Vulkan application necessarily fails |
| Pipeline log, 2026-10-16 | Recorded user confirmation of audible sound and character name; visual/performance/menu experiments | A substitute for dedicated acceptance gates for every feature |

Gate records were parsed rather than trusting their PASS label alone. Old artifacts may have been overwritten by
later runs; a record's hash is historical metadata, not a fresh hash verification in this audit.

## Task reconciliation

### Phase 0 — extraction milestone; incomplete reconnaissance

- **0.1:** v4.0.0 extraction has the dumps gate above. Base extraction, own-console key provenance and version
  decisions are documented in `phase-0-findings.md`; keys were not opened. Leave the composite provenance/base
  checklist open where the available gate does not prove it. `dumps/v400/` is the actual patched target.
- **0.2:** sizes/symbols/middleware/package inventory exist in findings. Instruction coverage has downstream
  evidence, but full reproducible service/NVN lists and version-tagged inventory remain partial.
- **0.3:** game-sized Ghidra/REA snapshot and reviewed main-loop/thread investigation are unverified.
- **0.4:** Eden visual comparisons are recorded; reproducible SVC/IPC reference capture remains open.
- Zelda dump comparison remains conditional on ownership/provenance; not a blocker for this game.

### Phase 1 — DLL/runtime path established historically; coverage unfinished

- **1.1-1.3:** historical fork/layout/exclusive-pair work retained; exclusive-pair evidence is narrowly scoped.
- **1.4:** pending integer differential tests sampled from the game's actual instructions.
- **1.5:** partial; new checked subtask 1.5a records the measured SIMD sample, not exhaustive semantics.
- **1.6:** historical generation/link milestone retained; old function-count claims are not validated by
  run_id=990a33212b. Use a version-tagged inventory for fresh counts.
- **1.7:** pending report/optimization; deterministic first-battle dispatch error is recorded as addressed
  in pipeline log 2026-10-15, commit `28c44eb`. Do not confuse it with rare loading crashes.
- **1.8:** unchecked pending a specific original-word patch-guard test.

### Phase 2 — historical M2; revalidation needed

- **2.1/2.2/2.6:** retain existing historical evidence for memory/layout/null backends.
- **2.3/2.4:** partial observed SVC/IPC support; no exhaustive service/kernel semantics claim.
- **2.5:** partial synchronization repairs; stress test and FIFO ordering remain open.
- **2.7:** pending structured Eden comparison.
- **Immediate audit follow-up:** reproduce/triage the latest failed headless build before asserting current health.

### Phase 3 — reading and save/load observed; atomicity not established

- **3.1:** partial: `services/fs.c:375-388` serves a raw romfs image (`<g_romfs_dir>.bin`), not the originally
  proposed extracted-folder backend. Extraction input and runtime representation are different layers.
- **3.2:** patched target exists; dynamic base/update layering in the runtime remains unverified.
- **3.3:** observed storage reads; asynchronous/parallel semantics and latency measurement remain open.
- **3.4:** manual persistence reported; Commit at `fs.c:568` is a no-op. Atomic/durable saves require separate work.
- **3.5:** parser and trace correlation remain pending; share the deliverable with 9.3 and 10.2 rather than duplicate it.

### Phase 4 — rendered scenes observed; exhaustive validation open

- **4.1:** observed NVN inventory; full comparison remains open.
- **4.2/4.3:** observed features exist (compute, indirect draws, transform feedback etc. in pipeline history),
  not universal backend coverage.
- **4.4:** full offline shader corpus, fuzz and SPIR-V validation remain open.
- **4.5:** disk pipeline-cache code found at `nvn/vulkan/device.c:222-253`; persistence/invalidation test remains open.
- **4.6:** diagnostic hooks exist; full LAS scripts/RenderDoc workflow is unverified.
- **4.7:** VRAM mirror observations exist; total budget and orphan-resource/lifetime validation remain open.
- Historical black-screen/text/tree/terrain notes are not current unresolved issues. Distance blur is a conditional
  refinement if the user identifies a problematic scene.

### Phase 5 — user-visible paths observed; composite tests open

- **5.1:** audio heard by user; actual observed path is audout PCM, not proof of the originally specified full audren mixer.
- **5.2:** keyboard observed; physical gamepad, remapping and stub expectations need their own checks.
- **5.3:** pending; inventory says Bink `.bk2`, so do not assume MP4/USM support solves the real path.
- **5.4:** clock services/debug clock observed; persistence and accelerated day/night semantics require scoped validation.
- **5.5:** observed boot support; account/focus/applet/dock behavior not exhaustively tested.
- **5.6:** character naming manually observed; Pokemon renaming not specifically tested.

### Phase 6 — historical 10-minute route; not general stability

- **6.1/6.2:** scripts/logs/frames exist; semantic checkpoints and automatic triage remain partial.
- **6.3:** continuous process, not a finite task that is permanently closed.
- **6.4/6.6:** profiling and measured optimizations exist; per-area/thread performance matrix remains open.
- **6.5:** scripted 600-second route has evidence; random exploration component remains open.
- **6.7:** deterministic dispatch fix recorded; rare first-battle loading failures are a separate deferred issue.
- **6.8:** warm-cache metrics exist; cold-cache measurements and display pacing remain open.
- **6.9:** 60 fps explicitly deferred by user; do not enable it as audit cleanup.
- Rare battle/locker-room crashes remain deferred unless deterministic/recurrent, per prior decision.

### Phase 7 — partial tooling

- **7.1/7.2:** `runtime/fnprof.c` and `recomp/sym.py` found; action diffs and full symbol/disassembly workflow unverified.
- **7.3:** memory search/poke unverified.
- **7.4:** run_auto frame collection exists; named LAS script suite not found in inspected project tree.
- **7.5:** hook documentation exists in `psvrecomp/README.md`; coverage unverified.
- Removed duplicate hooks entry previously numbered 7.6; retained 7.6 for game REA snapshots.
- **7.6/7.7:** generic harness exists, game snapshots/reviewed game findings unverified.
- **7.8/7.9:** naming database and Ghidra bridge pending.
- Crash-log copy/report recorded; interactive error-box behavior still needs manual confirmation.

### Phase 8 — application incomplete

- **8.1:** launcher/setup/build UI pending.
- **8.2:** partial; code and test observations exist, full acceptance including physical controller is unverified.
  Reopened checkbox rather than treating feature presence as complete validation.
- **8.3:** 60 fps deferred by user.
- **8.4:** widescreen/ultrawide pending.
- **8.5:** internal-resolution/FSR1/SMAA options exposed; combination matrix pending.
- **8.6-8.8:** LOD, study tools and future mod/save-editor ideas pending; proposals, not core blockers.

### Phase 9 — study deliverables open

- **9.1-9.7:** all remain open. Diagnostic discoveries in the pipeline log do not replace reviewed study notes.
  `docs/re/` was not found in this audit.
- Removed duplicate 9.8 (same Zelda comparison as 9.7); repaired accidental checklist indentation.
- Proposed map-oriented subset: 9.3 archive/index/scene references; 9.2 trace loading/unloading;
  only the loader/entity part of 9.1 and collision-related part of 9.6 as needed.
- Proposed later: battle damage/AI/Terastal, exhaustive allocator/middleware analysis, full render-pass study
  and Zelda comparison. Do not mark these deferred by user until agreed.

### Phase 10 — plan only

Every implementation checkbox remains open. Start with replacement of a small existing area.
Outer RomFS reads may identify only the package, not inner map resources; determine interception layer first.
Filesystem overrides do not automatically bypass inner integrity checks. No evidence connects the existing
hash-table crash to bad map ids. Proposed hook names are not existing APIs.

## Suggested next decisions

1. **First:** reproduce the headless build failure and establish an honest current baseline. No code fix is part of this audit.
2. **Safety:** assess save atomicity/recovery separately before destructive mod experiments; always use copied saves.
3. **For a custom platform:** merge 3.5 + 9.3 + 10.2 package work, trace one small scene (9.2/10.1), identify
   geometry/collision/spawn dependencies, then prove a reversible override with identical bytes.
4. **For a polished app instead:** prioritize 8.1, menu/controller acceptance and 8.5's settings matrix.
5. Keep existing user deferrals (60 fps, rare nondeterministic crashes). Discuss other postponements explicitly.
