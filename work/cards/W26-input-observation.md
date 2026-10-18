# W26 — Execute one bounded diagnosis, not another plan

You own one narrow slice in D:/Dev/REA. Preserve existing dirty files. No commits, other projects, user saves,
external configuration or unrelated process kills. English repository; PT-BR result. Parent freezes your scope.

The previous W24 CLI returned after three turns, without executing a command, because it speculated that its
remaining USD 2.92 could not cover local builds. There was NO actual API/budget limit. That delivery was rejected.
Do not ask for permission to do the already-authorized steps below, and do not return a plan instead of tools.
Local compiler/game duration is NOT itself Anthropic token billing. Respect the actual CLI cap; stop only on a
real failure, not hypothetical expense. This is NOT a request to finish the entire roadmap in one call.

Perform this exact bounded sequence:

1. First run a resource probe (python/psutil, ollama ps). If free RAM >=24 GiB and no loaded model, execute:
   python tools/workers/local_worker.py --task D:/Dev/REA/work/cards/W25-baseline-comparison.md
     --ctx D:/Dev/REA/lab/reports/W24-baseline-metadata.json D:/Dev/REA/docs/roadmap/baseline.md
     --out D:/Dev/REA/lab/reports/W25-baseline-draft.md --model qwen3.8:27b --num-ctx 8192 --lang markdown
   Wait for this one call. Keep JSON statistics. Unload ollama stop qwen3.8:27b afterwards, and check actual RAM
   release before any game. If RAM is below the conservative threshold, do not load blindly; record the measured
   blocker and proceed to the CPU-only source inspection. Do not kill another application's model server.

2. Read OUR psvrecomp/runtime/hle/input.c, not generated game code. The name-to-bit mapping is established;
   do NOT change it or guess another menu button. We lack the actual count/type of GetNpadState(s) requests.
   Add ONLY a minimal opt-in `PVR_TRACE_INPUT_HISTORY=1` log in fill_state that reports single versus batch calls,
   player id, requested count (1 for single), sampling id and button bits. Limit logging (first few calls plus
   changes, or a hard cap) so per-frame I/O cannot distort the whole test. Default behavior unchanged.
   This is verification instrumentation, NOT a fix to the suspected history semantics. Do not alter sampling,
   controller layout, historical samples, saves, rendering, button timing or SDK responses in this slice.
   If anything is unclear, inspect public reference source; do not upload private game-derived code/assets.

3. If source changed, rebuild the SAME Vulkan target and relink through actual gates:
   python tools/verify/gates.py run host --version v400 --backend vulkan --agent claude
   python tools/verify/gates.py run link --version v400 --backend vulkan --agent claude
   Ensure no owned/manual game process is running before build.

4. Run EXACTLY ONE diagnostic 60-second scenario on an expendable copied save, with environment
   LARECOMP_TRACE_SAVE=1 and PVR_TRACE_INPUT_HISTORY=1:
   python tools/verify/gates.py run window --version v400 --agent claude --seconds 60
     --save D:/Dev/REA/lab/save-safety/654ac0677f/sandbox
     --input-script 4000:A,12000:A,32000:X:500
   Preserve the gate failure if one occurs; don't retry it or switch buttons. Retain log/captures in ignored lab/
   under the actual run_id before a future test can overwrite them.
   Report actual single/batch counts/id behavior, trace observations and seed manifest preservation.
   A logged X bit is not proof that the game consumed a press edge, and zero writes are not milestone closure.

5. Review the Qwen draft against input JSON if generated. Append a factual pipeline-log row and short execution
   note (Qwen stats/verdict, actual diagnostic/gate ids, what remains unknown). Lint Markdown.
   Do not mark B-03/B-04 done. No game screenshots/raw saves/decompilation in cloud context or tracked files.

Return actual output evidence, not an offer to start. Wait for worker/build/game commands before exiting;
no unowned background test or promise that a print-mode session can resume itself.
