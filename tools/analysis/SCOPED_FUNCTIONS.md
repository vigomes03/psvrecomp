# Scoped two-function Ghidra entry

This complements the [synthetic call-site helper](README.md). It creates **candidate** caller/callee functions
from supplied compiled-symbol intervals, not recovered original names or proven canonical function boundaries.
The default W30 script remains synthetic-only. The separately tested scoped entry is for approved local R-01
experiments on hash-bound images under ignored lab/targets; keep every private output under ignored lab/.

## Controls and interface

From D:/Dev/REA:

```sh
python tools/verify/test_scoped_function_probe.py
python tools/verify/test_ghidra_call_probe.py
```

Five scoped controls exercise actual owned AArch64 assembly and the installed Ghidra/decompiler: independent
assembler-derived target/decompilation, non-call rejection, wrong target, a real third database-function mutation,
and an observed interior site not reached by entry-based static flow. The six original controls remain intact.
Accepted source-control artifacts: lab/analysis-probe-tests/scoped-4783e595f4/ and controls-654e694834/.
These are actual native tests, not invented game-gate records.

Python API in scoped_function_probe.py:
run_scoped_probe(binary_path, base_addr, call_site_addr, caller_start, caller_end,
callee_start, callee_end, work_dir, timeout_s=120) returns descriptive metadata.

Bounds are inclusive; starts and lengths are instruction-aligned. Input is restricted to owned lab/targets or
lab/analysis-probe-tests, output to owned lab/, and each nonoverlapping interval is capped at 16,384 bytes.
Use a fresh private work directory for each run: pseudocode files have fixed caller.c/callee.c names.
Private exceptions may include native logs; retain their full text locally and expose only a reduced status/type
to a cloud coordinator. Flat images are unrelocated; runtime pointer/import semantics are not established.
Broad analysis is disabled. Disassembly stays within the supplied interval union plus its included observed
call site; the real decompiler has ten seconds per candidate and is disposed after use. Existing owned-PID-tree
timeout and native-log retention are reused. No existing analysis project or input image is modified.

The Java script queries the real database function count. Python requires exactly two functions, an independent
expected callee target, matching bounds/language/base/site, a bounded instruction count, actual decompiler success
and nonempty output files that cannot escape the work directory. Function provenance is explicitly
supplied-symbol-intervals. Decompiler completion/nonempty C is not proof of semantic fidelity or original source.

## Observed-call seeding and limits

A supplied entry may not expose an observed interior call through static flow. Seed only that known instruction
with flow following disabled, retain entry_cfg_decoded_call_site and call_site_explicitly_seeded separately, and
never reinterpret the second flag as proof of the first. The real-input failure that motivated this control is
retained at lab/reports/W34-scoped-functions/actual-4e1d06e3/; the synthetic interior-site control reproduces it.

Likewise, an expected count is not a measured count. A mutation that adds a third real Ghidra function exposed
the initial constant-valued count; the script now uses FunctionManager.getFunctionCount() and the wrapper rejects
that mutation. Do not manufacture successful metadata from expected values.

## Actual private experiment

The approved parent phase applied this entry to the two W31 runtime-correlated candidate intervals. Input was
rechecked against the existing NSO loader's decompressed image and the historical DLL against its failed-run
hash. Only descriptive metadata was exposed to the cloud model; private C/instructions remain local.

Receipt: lab/reports/W34-scoped-functions/actual-2a53fe88/receipt.json.

- Two candidate functions and 619 decoded instructions were reported by the real engine.
- The observed call site's direct target matches W31's independent static/native correlation.
- Entry-based CFG did NOT reach the observed site; explicit site seeding was needed. Do not claim full CFG recovery.
- The decompiler emitted two local files. The caller output contains a warning marker; the callee output has no
  such marker. Neither was reviewed for semantic correctness, and marker absence is not a correctness proof.
- The image hash stayed unchanged. The native invocation took 4.958 seconds; that is not total implementation time
  or peak-memory measurement. No game or local model was started.
- Independent public-source review has no blockers: lab/reports/W34-scoped-functions/review-verdict.json.

No engine subsystem, root-cause repair, battle completion or full R-01 acceptance is inferred. Candidate-bound
validation, private semantic review and the actual scene/resource path remain separate work.
