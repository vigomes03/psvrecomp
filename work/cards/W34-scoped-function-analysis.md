# W34 — Scoped Ghidra analysis entry for two runtime-correlated candidate functions

Workspace D:/Dev/REA. Read CLAUDE.md. Verification-infrastructure exception, not a game/runtime change.
Parent owns tools/verify/test_scoped_function_probe.py, already authored/run RED (missing module). Do NOT edit
or weaken it or existing tests. Keep all other dirty changes. No model load, install, global config edits,
game launch, commits or pushes. YOU MAY ONLY analyze our SYNTHETIC fixture in this implementation task.
Do not read lab/targets, dumps, generated game C or private reports. Parent later owns the approved read-only
R-01 metadata/private-function experiment. Never upload private bytes/pseudocode to a cloud service.

## Own only

- New tools/analysis/scoped_function_probe.py and ScopedFunctionProbe.java.
- Narrow backward-compatible extension in tools/analysis/ghidra_call_probe.py, not a subprocess rewrite.
Default W30 CallProbeScript use remains synthetic-only. Add internal keyword-only _script_name=None and
_script_args=() to run_call_probe, using the existing SCRIPT_NAME at CALL TIME when override is None.
Append extra args after existing base/site/output-json arguments to the chosen post-script. Preserve its real
subprocess timeout/tree cleanup, freshness, logs, exceptions and old missing-script fault test.
Add optional raw_metadata field to CallProbeResult, populated from the actual parsed payload. Existing fields
and default behavior stay unchanged. No fabricated metadata or synthetic success fallback.

## New public interface

run_scoped_probe(binary_path, base_addr, call_site_addr, caller_start, caller_end,
                 callee_start, callee_end, work_dir, timeout_s=120) -> dict

Bounds are inclusive. Validate integer/aligned starts and inclusive ends, nonoverlapping caller/callee intervals,
call site inside caller, both intervals inside the raw image, each <=16,384 bytes. Restrict inputs to owned
lab/targets or lab/analysis-probe-tests and output to owned lab/. Reject before launch on invalid input.
Call the existing runner with the new script and extra arguments in this EXACT order:
base, site, output_json, caller_start, caller_end, callee_start, callee_end.
The old runner supplies the first three; append the four bound arguments. Return actual metadata with safe
absolute caller_pseudocode/callee_pseudocode paths under work_dir. Fail closed on wrong target, failed decode,
wrong function count/provenance, absent/empty decompiler outputs, unexpected paths or script errors.

## Java script contract

Fresh BinaryLoader project, import at zero and genuinely rebase as the existing tested script does. Verify
actual language AARCH64:LE:64:v8A and min-address mapping. Broad auto-analysis remains disabled by the runner.
Use DisassembleCommand restricted to each supplied interval; never follow disassembly outside their union.
Check the requested site is a direct call with exactly one target equal to supplied callee entry BEFORE
creating/decompiling functions. Non-call or different target is an error, never success.

Create exactly two USER_DEFINED candidate functions with the supplied bodies and names candidate_caller and
candidate_callee. These are explicitly SUPPLIED CANDIDATE BOUNDS, not recovered original names/body certainty.
Use the real installed decompiler with <=10 seconds per function and dispose it in finally. Write actual C
output to caller.c/callee.c under output_json's parent, never into the installation or an existing project.
Report ordinary existing probe fields plus function_count=2, function_provenance='supplied-symbol-intervals',
auto_analysis_disabled=true, caller_decompiled/callee_decompiled booleans, output paths, supplied bounds and
bounded decoded-instruction count. No instruction listing or C content in JSON/stdout. A failure may emit an
error JSON, which the existing runner must reject, with native failure logs retained.

## Public APIs verified by parent against installed source archives

- new DisassembleCommand(Address start, AddressSetView restrictedSet, boolean followFlow).
- cmd.applyTo(currentProgram, monitor), as used by FlatProgramAPI.disassemble.
- FunctionManager.createFunction(String, Address, AddressSetView, SourceType).
- DecompInterface.openProgram(Program), decompileFunction(Function,int,TaskMonitor), dispose().
- DecompileResults.decompileCompleted(), getErrorMessage(), getDecompiledFunction().getC().
- Existing GhidraScript toAddr, currentProgram, monitor, listing/flow APIs from CallProbeScript.java.
Installed headless executable: D:/Tools/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat. Read/execute authorization
is only for that exact installation; no edits/upgrades or adjacent-directory discovery. No need to inspect SDK.

## Acceptance

Exact authorized commands (no pipelines/redirects/wrappers/discovery):
python tools/verify/test_scoped_function_probe.py
python tools/verify/test_ghidra_call_probe.py

The new test assembles an ABI-correct owned ARM64 fixture, checks actual decompiler output and independent
assembler-derived call target, and rejects non-call/wrong-target cases through the real engine. Old six controls
must remain intact. Stop on the first permission denial; do not evade it. Wait for tests and return actual
results/paths or precise errors, not plans. Do not edit roadmap checkboxes or invent gate records.

## Parent verification / approved local input phase

The implementation CLI returned 18 turns with no permission denials and actual synthetic test output. Parent
then added two red-capable controls: a real third-function mutation exposed constant-valued count metadata,
and an interior-site fixture reproduced the first real-image attempt's missing call-site decode. The producer
now queries the database count and separately records entry-based decoding versus explicit observed-site seeding.
Five scoped and six original controls passed after those changes; independent public-source review has no blockers.

Only after synthetic verification, the parent applied the separately scoped entry to the hash-verified local
image and W31 caller/callee bounds, with no private C uploaded. First attempt failed and remains retained;
second receipt is lab/reports/W34-scoped-functions/actual-2a53fe88/receipt.json. Two candidate C outputs are local,
the caller contains warning markers, and entry-CFG reachability is explicitly NOT proven. R-01 stays open.
See [actual result and limits](../../docs/roadmap/scoped-analysis-2026-10-18.md).
