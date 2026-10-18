# W24 — Finish baseline acceptance with bounded Qwen assistance

## Authority, ownership and scope

User selected `qwen3.8:27b`, not Devstral, ONLY for tasks we judge suitable, and asked to finish milestone B.
Claude Code owns this bounded investigation. Parent freezes edits while you run and reviews the real results.
Work ONLY in D:/Dev/REA. Current branch is master; HEAD dede06c. Preserve ALL existing dirty changes.
No commit, push, reset, stash, original-save mutation, outside-project edits, installation, unrelated process kill,
Hermes configuration change, or relaxed acceptance criteria. Read CLAUDE.md and the project skill first.
Repository English; final summary PT-BR. No claim of closure without full recorded acceptance.

## Current facts

- B-01/B-02 have fresh evidence. B-03 metric routes passed; semantic/manual acceptance remains open.
- B-04 isolation, corruption recovery and old-save reload passed; NO real fresh guest save has been observed.
- Prior parent wasted time on speculative X/R/PLUS sequences. Do NOT repeat that strategy.
- The input.c name mapping itself agrees with its enumeration. No evidence supports the previous claims that
  saving requires a long X press, that R is the pause menu, or that the bit positions were wrong.
- Latest isolated Vulkan build run_id=4133097e1d; link run_id=8a1337f52a. Source fingerprints are enforced by
  gates.py; rebuild host AND relink after changes to runtime/header inputs.
- Runs f370aca5cd, fa575841b7, 3150efa2b4, 68774bcf5a, 7c211d64dd showed only two save reads, no writes.
  ce0623cacb also had no writes and failed a frametime threshold. Preserve its failure.
- Explicit input is logged by the runtime, but observing a bit in fill_state does NOT prove the game's action
  handler consumes a press edge. Trace the seam instead of guessing another key.
- Candidate worth checking (NOT a diagnosis): GetNpadStates in input.c fabricates count historical samples with
  identical buttons and descending sampling ids. Check reference semantics, actual count requests and the
  consumer's edge expectations. Also consider disabled in-game menu/tutorial state and input timing.
- Source seed (immutable): D:/Dev/REA/lab/save-safety/654ac0677f/sandbox, with save_0/main.
  All game experiments use the existing prepare_window_save helper into lab/host-vk-auto/save_gate.
- Previous trace logs/captures: ignored lab/b04-trace-attempts/<run_id>/; do not overwrite preserved attempts.
- Worker defaults are already Qwen in all three project harnesses, with thinking disabled for direct calls.
  `python tools/verify/test_worker_defaults.py -v` passed after reproducing all three old defaults as failures.

## First bounded delegation, then hard diagnosis

1. Delegate one SUITABLE short task to Qwen via tools/workers/local_worker.py, not a Hermes subagent: draft a
   B-03 route/coverage comparison from lab/reports/W24-baseline-metadata.json and the baseline criteria.
   Give a separate W25 card, exact draft output under lab/, no invented checkpoints or user approval.
   The supplied metadata contains measured counts and criteria, not game bytes/assets. Keep the draft short.
   Use explicit --model qwen3.8:27b and a small context (4096 or 8192 as measured prompt size allows).
   Before loading: inspect actual RAM/VRAM and loaded models. Do not start a game while Qwen is resident.
   The conservative free-RAM threshold is 24 GiB; below it, load only if a written measured small-context plan
   demonstrates headroom. Otherwise record the actual blocker. Do not close other applications to force a fit.
   Review the draft against source metadata, log model/tokens/time/verdict. Unload Qwen after the batch and
   recheck actual memory release, not just an empty `ollama ps` listing.
2. Claude retains difficult root-cause diagnosis. Read OUR runtime/input and relevant public reference code.
   Rank falsifiable hypotheses, identify a tight red-capable command, and measure the actual failing seam.
   Minimal opt-in diagnostics may help distinguish GetNpadState vs GetNpadStates/count/sampling behavior.
   Do not assert the candidate above is the cause without data. Do not edit game-derived C.
3. If a runtime fix is justified, obtain a failing native regression before the fix and a passing regression
   after. Delegate a bounded test/fix fragment to Qwen only if suitable and memory permits; otherwise record why
   Claude handles the hard diagnosis. No more than three retries, and no broad input/SDK rewrites.
4. Run the matching host/link/window gates on the actual changed source. A functional-save scenario must
   demonstrate actual guest write events and persistent file changes, not merely passing render/FPS checks.
   Compare source seed manifests before/after every run. Preserve every first-attempt failure.
5. Reopen a copy of the freshly guest-written save in the actual game. Record what establishes game acceptance.
   Test interrupted-write recovery only on expendable data and state the achieved guarantee precisely.
   Commit is currently a no-op; do not invent atomicity or add transactions without a demonstrated need.
6. Update B-03 route comparison and B-04 evidence with run_ids. Keep any genuinely human visual acceptance
   pending; no user response is not approval. Never lower the milestone criteria to claim closure.

## Privacy

Never read keys or upload raw dump bytes, save contents, game-derived C, Ghidra pseudocode, assets or screenshots
into cloud model context. Keep them local/ignored. Public reference source and OUR host runtime are allowed.
Local vision via Qwen is possible after checking capability/resources; no concurrent game/model workload.
Derive only descriptive metadata for review. Do not attach the full REA MCP catalog to a local model.

## Real commands and acceptance

- python tools/verify/test_worker_defaults.py -v
- python tools/verify/test_host_gate.py -v
- python tools/verify/test_runtime_freshness.py -v
- python tools/verify/test_save_safety.py -v
- python tools/verify/test_window_input.py -v
- python tools/verify/test_gates.py
- python tools/verify/gates.py run host --version v400 --backend vulkan --agent claude
- python tools/verify/gates.py run link --version v400 --backend vulkan --agent claude
- python tools/verify/gates.py run window --version v400 --agent claude --seconds 60 --save <immutable source>
  --input-script <one evidence-backed scenario>; set LARECOMP_TRACE_SAVE=1 for the child environment.

Use actual tools and logs, not plausible output. Do not hand-write gates.jsonl. New verification infrastructure
may use existing generic test gates only if their checks really cover the added test. Lint edited markdown.

## Exit contract

Wait for bounded child tests/worker calls before returning. Do not launch an unowned background game and promise
this print-mode session will resume after exit. If a test must outlive you, give its exact PID/start time/command,
configuration/logs to the parent explicitly; do not call that a finished acceptance.
Final PT-BR report: changed files, Qwen card and measured result, reproduced cause vs unresolved hypotheses,
commands/run_ids and failures, whether a fresh save actually changed and reloaded, criteria still open.
A concrete blocker is acceptable; another successful generic window run is not a substitute for a real save.
