# W23 — Continue the evidence-led REA pipeline

## Authority and scope

The user explicitly requested autonomous development through the new roadmap milestones, not just a plan.
Work ONLY inside `D:/Dev/REA`. Read `CLAUDE.md`, `AGENTS.md`, `.agents/skills/` and the active
`docs/roadmap/README.md`. This is a private local study of the user's own dump.
Do not touch Hospital, D:/HospitalTools, Hermes settings/skills/cron, other profiles or external installations.
Do not commit, push, stash, reset, delete prior evidence, or overwrite original dumps/saves.
Do not disable any safety/verification rules or use a different model as an unsupervised orchestrator.

## Current handoff (parent stops editing while you own this task)

HEAD: dede06c. Dirty changes are the parent's verified current batch, NOT junk to undo.
Read `docs/roadmap/execution-2026-10-17.md` and inspect git diff before edits.

- B-01 has host/shim evidence: 69f115de36 / dc8810b71b, failed reproductions retained.
- B-02 has pinned inputs 01d413a344, two 60-second boots 8e0e7bcf37, isolated Vulkan host/link bcba9b8984 / bc7adfe0bc.
- B-03 metric gates: isolated new game c5a424fa05; isolated restored-copy 600-second route 49191e3f3a
  (17168 frames, 28.8 fps final windows, original source manifests unchanged). Manual visual question timed out.
  Do not pretend the user confirmed screenshots, physical hardware, audio or semantic game checkpoints.
- B-04 backup/restore gate e51fe74c5b, including synthetic abrupt-exit tests, actual private copy corruption/restore.
  Reload of the restored old save has 49191e3f3a. Actual GUEST write/rename/flush/Commit sequence and persistence of
  a freshly written save are still open. Source handlers alone do not establish the guest's sequence.
- REA Windows adapter explicitly rejects raw ARM64 (only PE/raw6502 in this build). Do not repeatedly retry it or
  modify upstream ref/rea to suppress the guard. Direct installed Ghidra headless CAN import the private raw image:
  `lab/targets/v400-main-709bfd6611529864.bin`, base 0x7000000000, language AARCH64:LE:64:v8A,
  BinaryLoader/default compiler spec. Existing project in `lab/ghidra-projects/v400_main_709bfd6611529864`.
  Auto-analysis was disabled; no observed loader call chain exists yet. Read the private command log only through
  bounded local tooling; raw/decompiled game output must not enter cloud-model context or tracked docs.
- No game or analysis process from the parent remains running. Never assume this stays true; check ownership before
  a build, delete, or run. Automated Vulkan host is `lab/host-vk-auto`; never overwrite the manual host for testing.

## Work order

1. First finish the AUTOMATABLE B-04 gap with copied saves only. Investigate the real guest save flow. Minimal opt-in
   tracing of host file commands can be appropriate, but inspect real APIs and root causes first. Do not assume a
   menu key sequence causes a save: demonstrate actual write/flush/rename events and persistent file changes.
   Restore/reopen a test copy with the actual game, preserving original seed hashes. Record achieved guarantees and
   remaining power-loss/atomicity limitations. Do not add a host transaction system without evidence it is needed.
2. Leave manual B-03 acceptance pending without stopping to ask the user again. Continue independent read-only R work
   or another safe app subtask where prerequisites are genuinely satisfied; never bypass prerequisite safety gates.
3. Continue the active roadmap R -> C and the independent A track, ONE bounded work card at a time, until all
   automatable acceptance is evidenced or a concrete blocker/turn/budget limit prevents safe progress.
   Do not stop after the first success. Do not promote hypothetical resource formats, collision or scene ids.
   No 60 fps work; rare nondeterministic crashes remain under the recorded user deferral unless a true blocker.

## Worker and privacy contract

Claude orchestrates; use `tools/workers/local_worker.py` / `tools/rea/rea_worker.py` for bounded execution when
resources fit, and verify every result. No Hermes subagent worker. Recheck Ollama models and available RAM before
loading anything; previous available RAM was below the conservative 24 GiB worker threshold.
Do not close/kill unrelated user apps or modify their settings to free resources. Log an exception or real blocker
rather than loading a heavy model blindly. Use small context only when a measured resource plan justifies it.
Do not expose ROMs, keys, private save contents, decompressed game bytes, game-derived C, Ghidra pseudocode or assets
in cloud prompts, tracked files, stdout summaries, uploads or external APIs. Keep raw outputs under ignored lab/.
Use existing local tools to reduce private results to descriptive metadata. Never read key files.

## Acceptance and reporting

- Tests before fixes; actual gates and run_ids for builds/link/boot/gameplay, no made-up success or handwritten gate records.
- Preserve failing first attempts. Metric screenshots are not semantic/manual approval. Any worker claim needs review.
- Existing helpers/tests: tools/verify/test_host_gate.py, test_save_safety.py, test_shortcuts.py, test_nso_verify.py,
  test_gates.py. `gates.py run host/link --version v400 --backend vulkan` uses lab/host-vk-auto;
  window uses that isolated host; save_safety --save takes an immutable seed and exercises expendable copies.
- Update active roadmap checkboxes ONLY at their full acceptance; keep partial subtasks explicit, no fake totals.
- Append factual results to docs/pipeline-log.md and execution notes. English repo text, PT-BR final summary.
- Final report must identify exact changed files, actual commands/results/run_ids, task ids advanced, remaining manual
  or technical blockers, resource/model failures and dirty git status. No claim that all milestones finished unless
  every acceptance criterion actually has evidence. No commit/push.
