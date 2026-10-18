# W32 — Capture Windows native fault context before the existing fatal reporter

Workspace D:/Dev/REA. Read CLAUDE.md. Verification-infrastructure exception: a narrow diagnostic helper, not a
speculative game fix. Existing dirty files and all source/save inputs must be preserved. No Qwen/Ollama load,
no game/Ghidra launch, no global setting/install changes, no commits/pushes and no private game data reads.

## Own exactly these edits

- New psvrecomp/runtime/platform/windows_fault_context.h.
- In psvrecomp/runtime/platform/windows.c: its include and one call at the start of unhandled_filter, BEFORE
  its old stack-top dereference and rt_fault_report. Do not change lazy_commit, vectored recovery or fatal behavior.
- Do NOT edit tools/verify/test_windows_fault_context.py or weaken its assertions. Parent owns it.

## Existing interfaces and oracle

Parent authored tools/verify/test_windows_fault_context.py first and ran it: expected RED, missing header.
It compiles the REAL production windows.c with function/data sections and garbage collection. Only final
rt_fault_report termination is intercepted by the C fixture; real OS read/write/execute faults enter the
production unhandled_filter and must emit context BEFORE that terminal boundary. The normal path stays silent.
The exact authorized verification command is:
python tools/verify/test_windows_fault_context.py

Public Windows APIs/fields are already used by windows.c. Implement static inline
pvr_print_windows_fault_context(FILE *stream, const EXCEPTION_RECORD *er, const CONTEXT *ctx).
Classify memory access only for EXCEPTION_ACCESS_VIOLATION or EXCEPTION_IN_PAGE_ERROR with >=2 parameters:
ExceptionInformation[0] is 0=read, 1=write, 8=execute; [1] is the fault address. Other codes/short records must
report access=unknown valid=0 (not fabricate valid access information). Unknown operation values stay unknown.
Reference: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-exception_record

Output lines start [host-context]. Include exception code, access name, valid=0/1, raw operation if valid,
address as 16-digit lowercase hex, and these actual 64-bit CONTEXT register values as name=%016llx:
rax rbx rcx rdx rsi rdi rbp rsp r8 r9 r10 r11 r12 r13 r14 r15 rip. Flags are useful too.
Explicitly cast 64-bit printf args to unsigned long long. Use no allocation, no guest-memory/stack
reads, no decoder, and no instruction dumps. Flush the stream before returning, preserving diagnostics if
later existing reporter code itself faults. No change to how the exception terminates.

## Task execution

Read the test and the relevant source, implement the minimal header/include/hook, then run the EXACT test
command (no pipelines, redirects, environment wrappers or directory discovery). No need to inspect installations.
Compiler is already known at D:/msys64/ucrt64/bin/clang.exe; test chooses its own environment.
On any permission denial, STOP and report it; do not try alternate wrappers. If fixture compilation reveals
an unrelated existing-source issue, return the exact output to parent instead of editing other runtime code.
No long background job. Return actual test outcomes and changed paths, not a plan. Parent owns full host/link
gates and gameplay acceptance. This change does not claim to fix the historical B-03 crash.

## Review-driven narrow follow-up and acceptance

The reviewer identified an existing secondary-fault risk in the same reporter's saved-stack heuristic.
Parent reproduced it with a committed PAGE_NOACCESS saved RSP before changing production code (two exception
reports), then replaced only that best-effort read with same-process ReadProcessMemory plus an exact-byte-count
check. Fatal behavior remains unchanged. Readable/NOACCESS/GUARD/cross-page controls now pass without a second
exception. The actual platform.h noreturn declaration resolves the review's missing-return conditional concern.
Final evidence: run_id=240fe07924 (Vulkan host), run_id=af480d2048 (link), run_id=74fcd35f8b (window).
Six native controls and a fresh independent review have retained receipts in lab/reports/W32-fault-context/.
See [scope, controls and limits](../../docs/roadmap/windows-fault-context-2026-10-18.md).
