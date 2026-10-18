# Pipeline execution — 2026-10-17

Active scope: B baseline, then R/C scene/platform work; app acceptance A is a separate track.
30 fps is retained. No deferred 60 fps feature is enabled. See the [roadmap](README.md).

## B-01 — headless regression

- Reproduced the failure against the current source: run_id=5bca0b86c4 (FAIL).
- Added a regression assertion for the missing driver-query entry point: run_id=9ace5ba6d7 (FAIL).
- Root cause: `services/audio.c` logs SDL_GetCurrentAudioDriver, but the no-device shim lacked that symbol.
- Minimal fix: the shim returns NULL (no audio driver); it does not simulate a working audio device.
- Targeted shim plus audio source check: run_id=dc8810b71b.
- Fresh headless host artifacts: run_id=69f115de36.
- Fresh v4.0.0 boot, two 60-second attempts with real frame/time-limit markers and no recorded exception/FATAL:
  run_id=8e0e7bcf37. This is not an arbitrary-service or whole-game proof.

Implementation was a three-line shim addition; tests/gate infrastructure were maintained directly.
No local model was loaded alongside the game baseline; resource constraints from the previous measured
18.27 GiB free versus the worker's conservative 24 GiB threshold remain a reason not to run a heavy worker blindly.
No worker-generated result is being claimed in this batch.

## B-02 — input and runtime identity

Pinned v4.0.0 exefs/nonempty romfs recheck: run_id=01d413a344.
`layout.py` output and `lab/host-v400/boot_run1.log` agree on the following ids/bases:

| Module | Build id prefix | Guest base |
|---|---|---|
| main | `709bfd6611529864` | `0x7000000000` |
| subsdk0 | `310fad4782253cab` | `0x7004800000` |
| sdk | `bb560bdfa85b4a97` | `0x7005000000` |

The fresh boot reports 233,128 functions; do not carry forward the old function count.
The gate records source revision `dede06c` with dirty state for the current edits and hashes of the actual outputs.
Initial Vulkan host/link evidence: run_id=3d82811262 and run_id=bc4d4c6213.
The linked object directories contained 1,234 main, 119 subsdk0 and 156 sdk objects.

The first compatibility reruns used the legacy `lab/host-vk` while no manual game process was present;
manual save/settings were not selected. The updated host/link/window gates target isolated `lab/host-vk-auto`
for subsequent automation. Fresh isolated host/link: run_id=bcba9b8984 and run_id=bc7adfe0bc.
A 60-second isolated new-game metric run has run_id=c5a424fa05; source-save preparation was also checked.

## B-03 — gameplay evidence

Fresh 60-second new-game metric gate: run_id=18c9b702ee, first attempt, 1,641 frames, 7/11 rendered frames,
10 scene changes, final windows 28.7/28.3 fps. Log and frames were copied before the next run to
`lab/baseline-20261017/new-game/`.
This does not semantically identify a title screen, confirm name entry, or prove character control.
The requested semantic/visual confirmation remains separate from metric gates.

The 600-second copied-save route has run_id=64b1817ee3: first attempt, 17,167 frames, no FATAL/exception,
111/114 rendered screenshots, 29 scene changes and final windows 28.9/28.9 fps. The original seed hash was
rechecked unchanged. The metric gate took 782.1 seconds including capture/stat processing, not 782 seconds of gameplay.
Its log/frames were preserved under `lab/baseline-20261017/open-world/`. The isolated 600-second run from the
restored copy has run_id=49191e3f3a: 17,168 frames, 111/114 rendered screenshots, no recorded FATAL/exception,
final windows 28.8/28.8 fps, and identical source manifests before/after the game. Evidence was copied to
`lab/baseline-20261017/isolated-restored-open-world/`.
The user visual-confirmation request timed out without a response; B-03 remains open, not implicitly approved.

## B-04 — safety contract, not atomic saves

**Current acceptance:** the later chain has run_id=f933f43273, run_id=4ec8dcdc29, run_id=a9bef169e1,
run_id=7ea127f858 and run_id=d6946b460e. See the [recovery policy](../save-recovery-policy.md).
The following initial checks and W23 notes preserve the chronological pre-acceptance state.

Source audit: `runtime/services/fs.c` writes via pwrite, exposes file Flush via fsync, forwards rename,
and handles filesystem Commit as a no-op. That identifies the host handlers, not the game's actual write order.
The existing `[save]` logging filters for "savedata" and does not establish the sequence for this game's `main` file.
No host transaction mechanism has been added without first observing that sequence.

New save preparation rejects source/target overlap and missing inputs before deletion; it verifies a staging copy
before replacing the expendable sandbox. Copy paths must remain under project `lab/`; linked save entries are rejected.
Window gates now record source-save manifests and compare the original after the game exits.

Backup/recovery gate: run_id=e51fe74c5b. It ran four synthetic regression tests including abrupt process exit,
then copied the actual private seed to a backup/sandbox, deliberately damaged only the expendable copy,
restored it from backup and checked byte hashes and original-seed preservation.
The recovered copy is retained under the gate record's private `restored_sandbox` path for a game reload check.
This is a backup policy demonstration, not a power-loss or atomic guest Commit guarantee.
A game reload/600-second route of the restored copy has run_id=49191e3f3a. Actual guest write-order and
a freshly written save/persistence scenario remain open; successful parsing of a restored old save does not prove those.

### Guest save write-order tracing (continuation)

Root cause for the still-open guest sequence: `runtime/services/fs.c` filtered save read/write logging on a
literal `strstr(f->path, "savedata")`, but the real mounted path is `<save_dir>/save_<type>/...` (e.g.
`save_0/main`, matching the hash seen in the backup/recovery gate) — the substring never matched, so the filter
was dead code and no `[save]` line could ever have been produced for this game's actual save files. `Flush`
(IFile cmd 2), `Rename` (IFileSystem cmd 5/6) and `Commit` (IFileSystem cmd 10) had no logging at all.

Fix: tag `HostFs`/`HostFile` with a real `is_save` flag set where the save filesystem is actually opened
(fsp-srv `OpenSaveDataFileSystem`, cmd 51/53), not a path substring; `sdcard` (cmd 18) is explicitly `false`.
Added opt-in tracing (`LARECOMP_TRACE_SAVE=1`, off by default, zero behavioural change otherwise) on
`CreateFile`/`Delete`/`Write`/`Flush`/`Rename`/`Commit` for save-tagged handles only. `Commit` stays the
existing no-op host handler; the new line only documents that the host observed the guest's Commit call, it does
not add a transaction system.

Verification of the code edit so far:
- The null host build has run_id=2e8186cc0a. This does not rebuild Vulkan.
- Existing host/save/gate tests passed, but they did not exercise the new filesystem trace paths.
- Window run_id=8ec8ad832d is a metric result from the older Vulkan binary. Its zero `[save]` lines
  are **not** evidence of absent save I/O. The same limitation applies to the subsequent long rerun.
- Guest write-order during a real save event remains unobserved. See the corrective validation below.

## W23 review and corrective validation

The Claude Code session ended normally after 56 turns; this was a partial delivery, not the end of the roadmap.
It added save-mount classification and opt-in `LARECOMP_TRACE_SAVE` instrumentation in `services/fs.c`.
Its headless host check has run_id=2e8186cc0a. The old hooks now reached for save files are neutral no-ops
(`runtime/hle/las_hooks.c`); SD-card mounts remain excluded by the new boolean classification.

**Rejected interpretation:** the W23 60-second window run (run_id=8ec8ad832d) used an older Vulkan executable;
only the null host had been rebuilt after the filesystem edit. Zero trace events in that run cannot establish
anything about real save I/O under the new instrumentation. Its longer background run has the same provenance
limitation. These are not accepted save-protocol proofs, even if their generic window metric gates pass.

Parent correction: host gates now record hashes of runtime/header/build inputs and verify that inputs did not
change during the build. Window gates require both matching executable hash and a successful Vulkan host record
with the current source manifest. The stale runtime was rejected before any game/save preparation by
run_id=47dffdf519 (FAIL). Four freshness unit cases and two input-isolation cases cover this boundary.

Window acceptance also supports `--input-script`, passed as an environment value rather than shell text, with
periodic default presses disabled and the test ini forced. A deliberate menu/save-button experiment is being
run only after the prior W23 gate exits and a real Vulkan rebuild/link; no guest save is assumed until write,
flush/rename/commit events and copied-save persistence are observed. B-04 remains open.

## B-04 final acceptance and B-03 remaining scope

Actual menu navigation, rather than another guessed shortcut, produced write/Flush/Commit in run_id=f933f43273.
Local native Windows OCR established the menu entries and the earlier tutorial modal; hardware/model memory
was not required for this screen-text check. The original source remained unchanged.

Fresh guest-save backup/corruption/restore has run_id=4ec8dcdc29; actual game reload has run_id=a9bef169e1.
A test-only fault boundary after host pwrite and before guest Flush/Commit was checked with native positive and
negative controls. The first scenario, run_id=30cee1fb8b (FAIL), used acknowledgments for the old tutorial state
and reached no write. The corrected fresh-state scenario has run_id=7ea127f858: one child, exit code 86, one fault
marker, actual write, no Flush/Commit, exact restoration and original-source preservation. Normal window runs
clear the fault flag rather than inheriting it from the shell. No transaction implementation or power-loss test
is claimed. New host/link evidence is run_id=6ca1db9532 and run_id=57eeeefd76.

The post-interruption restored copy was loaded normally in run_id=d6946b460e: first attempt, 1,621 frames,
9/11 rendered captures, four scene changes, final windows 28.9/28.9 fps and unchanged source manifest. The loaded
bytes matched the pre-interruption checkpoint; native OCR found the expected menu options. Private evidence is
retained under lab/b04-trace-attempts/d6946b460e and lab/reports/B04-acceptance-chain.json.

B-04 is accepted within its [documented backup policy](../save-recovery-policy.md), not a promise of atomic
writes. B-03 remains open: see the [metric comparison and semantic gaps](baseline-route-comparison.md).

## B-03 fresh first-battle blocker

The pre-battle copied-save route has run_id=e5b2041956 (FAIL): first-child host access violation at 0x8,
last presented frame 363. The wrapper retried and a later child reached 5,113 frames with no final-child
FATAL/exception and final windows 29.0/29.3 fps; the overall gate remains failed because the first attempt failed.
Source-save preservation passed. Logs/frames and bounded OCR observations are retained in
lab/baseline-20261017/first-battle-e5b2041956/. Battle completion and user visual approval are not claimed.

Do not broaden D-02 crash work without an identified cause or silently promote the retry to baseline acceptance.
The chosen B-03 route is explicitly blocked; independent read-only R-01 work remains permitted by the roadmap.

## R-01 — analysis entry probes

- The binary-layout probe returned capability_unavailable: its pwntools artifact profile supports Linux x64 only.
- Direct Ghidra analysis of the compressed NSO returned unsupported binary format.
- Alternative prepared: decompressed, unrelocated main module image in ignored `lab/targets/`, with build id and hash;
  the REA raw ARM64 probe confirmed a Windows-adapter restriction: native PE and raw 6502 only in this build.
- Alternative executed: the installed Ghidra headless launcher directly imported that raw image with BinaryLoader,
  language `AARCH64:LE:64:v8A`, compiler spec `default` and base `0x7000000000`. The existing PrepareRaw pre-script
  decoded/created its entry and the project was saved under ignored `lab/ghidra-projects/`; direct process exit 0,
  import/save markers checked in `lab/reports/v400-direct-ghidra.stdout`. Auto-analysis was deliberately disabled.
  This establishes an alternative import entry, not a full REA bridge, function corpus or observed loader call chain.
  A flat image is not a relocated runtime image or a
  section-aware ELF, and cannot establish every pointer/reference without further validation.

Raw outputs and any snapshot stay in ignored `lab/reports/` and `lab/snapshots/`, not this document.
No reviewed loader/resource call chain is claimed yet.

W30 attempted a small synthetic direct-Ghidra call-site probe, not private game analysis. The child repeatedly
requested installation-directory listings outside the project and received permission denials. Parent stopped
the owned process rather than continuing the authorization-probing loop; no new probe source/test result was
produced and no Claude/Java/game process remained. R-01 still needs its real function-analysis evidence.
Any additional installation-directory access requires explicit scope authorization; no global setting was changed.
The initial read/execute-only authorization request received no response. The user subsequently explicitly
approved the existing Ghidra installation. A delegated preflight with only that additional directory read
application.version=12.1.4 and executed the headless usage command with no permission denials. Its usage exit 1
is expected for missing project arguments, not an analysis result. Receipt:
lab/orchestration/W30-ghidra-access-preflight.jsonl. Installation edits/upgrades and other external directories
remain outside scope. The access blocker is resolved; R-01 function/call-chain acceptance is still pending.

### W30 synthetic controls accepted; R-01 remains open

The authorized exploratory retry ended at its CLI turn limit with repeated denied compound/discovery commands;
its partial source was not accepted as a finished delivery. Parent verification review found and reproduced two
semantic errors: BinaryLoader block placement was mistaken for the program image base, and the fixture's global
callee left an unresolved CALL26 relocation. The parent corrected both under the verification-infrastructure
exception, added real positive/negative/error controls, and fixed timeout handling: killing only cmd.exe had
waited 3.336 seconds for its JVM despite a 0.5-second limit. Owned-tree termination returned in 0.65 seconds in
the accepted delegated run. No processes were killed by name.

`python tools/verify/test_ghidra_call_probe.py` then passed six tests through a narrowly authorized CLI session:
10.337 seconds, zero permission denials. The parent verified actual tool-result content and retained JSON, not
just the model's report. Evidence is under `lab/analysis-probe-tests/controls-75012ab6e6/`; the exact-command receipt
is `lab/orchestration/W30-exact-controls.stream.jsonl`. Positive control resolved BL at 0x100004 to 0x100010 and
function FUN_00100010; the MOV negative control reported no call/target/function. Real missing-script and timeout
faults are rejected. No Claude/Java/game process remained at the verification check. Peak memory was not measured.

A fresh isolated source reviewer returned no blocking findings in
`lab/orchestration/W30-independent-review-isolated.json`; its actual JSON verdict was parsed and checked.
The earlier review attempt hit a turn limit after unrelated MCP discovery and is not the accepted review.
Source and reproducible procedure: `tools/analysis/README.md`. No game/private-target analysis, new gate records,
runtime changes or claim of a reviewed real loader/resource chain belongs to this slice.
