# R-01 scoped real-image entry — 2026-10-18

## Evidence, not milestone closure

W34 applies a separately tested local Ghidra entry to the caller/callee intervals associated with the historical
B-03 failure run_id=e5b2041956. This is beyond W30's synthetic-only readiness, but it is not a recovered scene
loader, a root-cause fix, human gameplay approval, or reviewed original-source reconstruction. R-01 remains open.

## Scope and input identity

- The historical DLL was checked against the failed run's recorded hash using the W31 archived copy, not the
  newly rebuilt window host. The existing private flat image was hash-compared again with the current NSO
  loader's decompressed image; its input build id starts 709bfd6611529864. Input hash stayed unchanged afterward.
- The two supplied candidate intervals came from the historical compiled guest-symbol ordering: 10,116 bytes
  for the caller and 1,024 for the callee. They are candidate bounds, not proven canonical machine-function bodies.
- Ghidra imports a fresh raw image at zero and verifies the actual rebase to the observed module base. The image
  is still flat/unrelocated; section permissions, runtime absolute pointers/imports/types are not recovered by this.
- Broad analysis is disabled, explicit intervals are capped at 16,384 bytes each, each candidate decompilation
  has a ten-second limit, and the owned headless process has a separate timeout/cleanup boundary. No existing
  private project is modified. Only descriptive metadata, not private C or instruction listings, reached cloud models.

## Actual outcome and limitation

Accepted local receipt: lab/reports/W34-scoped-functions/actual-2a53fe88/receipt.json.

| Observation | Actual result |
|---|---|
| Requested observed call site | 0x7002fdd678 |
| Direct target | 0x7002fdec10, consistent with W31's independent native/static correlation |
| Database function count | 2, queried from Ghidra rather than filled from expectations |
| Decoded instruction count | 619 |
| Function provenance | USER_DEFINED supplied-symbol-intervals, named candidate_caller/candidate_callee |
| Entry-CFG decoding reached the call site | False |
| Explicit observed-site seeding | True; only that instruction is seeded without flow following |
| Decompiler output | Two private files: caller.c (68,429 bytes), callee.c (6,404 bytes) |
| Warning-marker inspection | Caller has a warning marker; callee has none; neither is a correctness verdict |
| Native invocation elapsed | 4.958 seconds; not implementation wall time or measured peak memory |

The first real attempt failed closed because entry-based static flow did not decode the observed call site.
That attempt and its native error JSON remain at lab/reports/W34-scoped-functions/actual-4e1d06e3/.
A new synthetic interior-site control reproduced this limitation before explicit-site seeding was added.
The successful second attempt retains the false entry-CFG flag: seeding a known BL does not establish that
our supplied entry/bounds recover its true dynamic path. Do not silently reinterpret this as full CFG recovery.

## Verification and review

Reproducible public procedure: [scoped analysis entry](../../tools/analysis/SCOPED_FUNCTIONS.md).
Five new owned-fixture tests and six original call-site controls ran through the real installed engine.
The new fixture preserves the ARM64 link register around its call, and expected targets come independently
from the assembler's symbols. Negative cases cover non-call, wrong target and an actual third database function.
That last mutation exposed the initial constant-valued count; native metadata now queries the real count and
rejects the mutation. Acceptance uses actual native tests and returned metadata, not model summaries.

Accepted source-test artifacts: lab/analysis-probe-tests/scoped-4783e595f4/ and controls-654e694834/.
The fresh public-source-only review has no blocking findings:
lab/reports/W34-scoped-functions/review-verdict.json. All private pseudocode remains under the ignored actual
experiment directory, with hashes/byte counts in its receipt. It has not been supplied to a cloud reviewer.

## Remaining acceptance

Validate the candidate bounds/flow and semantic roles before relying on the decompiled C. The caller's warning
and missed entry-to-site path remain explicit limits. No semantic local-model review ran in this slice; Qwen
was kept unloaded following the earlier memory-pressure issue. The actual scene/resource path is still unknown.

Separately, W33 reviewed three retained gameplay captures through native OCR and enlarged crops. Recognition
was insufficient to establish an end-of-battle checkpoint or substitute for human B-03 visual acceptance.
No new button guesses, game run, runtime edits or fabricated game-gate records were introduced by W33/W34.
