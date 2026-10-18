# W32 — Windows native fault context and reporter safety

## Scope and boundary

W32 adds observability to the B-03 investigation, not a fix for the game's historical access violation.
The original run_id=e5b2041956 remains FAIL. Neither that failure nor B-03 semantic acceptance is cleared by
new clean runs. Qwen remained unloaded; no private game source/pseudocode was sent to the implementation or
review sessions, and no original save, global configuration or external installation was edited.

## Runtime changes

- psvrecomp/runtime/platform/windows_fault_context.h prints the supplied Win64 exception/context fields before
  the existing terminal reporter runs: access type/validity, fault address and integer registers including RIP/RSP.
  It does not dereference guest buffers, instruction bytes or the saved stack. Output is flushed immediately.
- The production unhandled_filter calls it before its previous stack-top heuristic. Successful vectored
  lazy-commit/watchpoint recovery remains silent and unchanged; normal execution has no new diagnostic output.
- Review found the old heuristic trusted MEM_COMMIT alone, then directly dereferenced saved RSP. A committed
  PAGE_NOACCESS region reproduced a second exception inside the reporter. The test observed two context reports
  instead of one. This is a reporter defect, not evidence that it caused the original game's failure.
- The heuristic now uses ReadProcessMemory on the same process and accepts only a full-size read. Otherwise it
  reports an unknown stack-top value (zero). Tests cover readable sentinel preservation, NOACCESS, PAGE_GUARD and
  a read crossing into a protected page, without a second exception in this tested environment.
- rt_fault_report's visible platform.h declaration is noreturn. Fatal termination/recovery policy was not changed.

The access-record interpretation follows the public Microsoft EXCEPTION_RECORD contract, referenced in the header.
Native contexts and private game-derived reports remain local under lab/.

## Native controls and review

Reproducible command: python tools/verify/test_windows_fault_context.py.

Six native tests passed; final retained output is lab/reports/W32-fault-context/final-native-tests.stderr.txt.
The fixture compiles the production windows.c, not a fake replacement filter. Real hardware read/write/execute
faults must reach the production filter and print the context before an intercepted final termination boundary.
The fixture's unrelated linkage boundaries terminate with distinct failure codes if unexpectedly called.
Additional controls exercise malformed/other exception records, full-width values, the silent normal path,
removal of only the production hook, and the four saved-stack cases. The saved-stack case exposes the unchanged
filter body through a test-only wrapper and supplies controlled contexts; it is not called a real game crash.

Initial test linkage needed two unrelated runtime boundaries supplied by the fixture; production code was not
modified to hide those unresolved symbols. The first independent review's nonempty concern lists were rejected
as an acceptance verdict despite its inconsistent passed=true flag. Its stack-read concern was reproduced and
fixed. The missing-return concern was checked against the actual noreturn declaration instead of changing the
termination contract. A fresh review of the final source/context has empty blocking lists:
lab/reports/W32-fault-context/final-review-verdict.json. Suggestions remain non-blocking, not established defects.

## Final source-bound gates

| Stage | Evidence |
|---|---|
| Final Vulkan host build | run_id=240fe07924, source manifest includes the new header and final Windows source |
| Final game-DLL link | run_id=af480d2048 |
| Final 60-second copied pre-battle regression | run_id=74fcd35f8b |

The final window record reports its first attempt clean, no FATAL/host exception, last periodic frame counter
1,646, 8/11 rendered captures, six image-metric scene changes and final FPS windows 29.1/29.0. Source-save hashes
are unchanged. These are metric checks, not proof of battle completion, human visual acceptance or stability.
No historical failure was hidden behind the retrying wrapper: the recorded first-attempt check is true.

Intermediate host/link/window records (f3e5766e1b, 11382bad39, 920472501d) predate the reporter hardening.
They are not used to certify the final source. The old host provenance was rejected after each source change,
and the same Vulkan backend was rebuilt/relinked before the final window check.

Final receipts: lab/reports/W32-fault-context/final-gate-records.json. Selected native log/captures and the full
window record were hash-checked and archived under lab/reports/W32-fault-context/accepted-window/.
Historical W31-matching binaries remain in lab/reports/W31-crash-triage/repro-2c0b6b48/host/;
do not symbolize that old failure against the newly rebuilt lab/host-vk-auto binaries.

## Remaining work

A future occurrence of the actual B-03 crash can now retain native registers and access type before terminal
reporting. No such game failure was captured by W32: both observed window regressions were clean. The game's
invalid read, the relevant functions' semantic roles and the required R-01 private-function analysis remain
unresolved. Do not add a game null guard or claim the new reporter safety change repairs that cause.
