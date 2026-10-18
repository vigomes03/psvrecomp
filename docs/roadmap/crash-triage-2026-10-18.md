# B-03 crash triage — 2026-10-18

## What changed in the evidence

The failed first child of run_id=e5b2041956 is now bound to an identified compiled symbol and a consistent
caller/callee pair. No runtime fix or engine-subsystem name is inferred. B-03 and R-01 remain open.
The previous tool-only R-01 evidence is supplemented with real runtime metadata, not replaced by a claim that
Capstone analysis is Ghidra function analysis or that the scene/resource loader is understood.

## Provenance before interpretation

- At W31 verification time, lab/host-vk-auto/pvhost.exe and pvgame.dll matched the hashes of run_id=e5b2041956;
  the same hashes were rechecked after symbolization. The host build reference is run_id=6ca1db9532.
- The original first-child crash log and its archived run1 log contain the same exception and native fault RVA.
- The existing flat main image is byte-hash-identical to Nso.image decoded from dumps/v400/exefs/main by
  the existing project environment. Its build id begins 709bfd6611529864; no filename-only version assumption
  was used. The verified input remains an unrelocated flat image, not a section-aware relocated program.
- No bytes, private assembly listing or generated game source are reproduced here. Local full receipts:
  lab/reports/W31-crash-triage/provenance.json and raw-image-provenance.json.

## Confirmed narrow correlation

| Observation | Evidence and interpretation |
|---|---|
| Host exception | The historical child recorded c0000005 accessing 0x8. |
| Containing compiled symbol | DLL RVA 0x1c0c1de is in f_7002fdec10's native text-symbol interval, offset 0x56e from its start. |
| Native operation | The instruction at that exact native PC is movswq: a sign-extending 16-bit load. This narrows the failing operation, not the lifetime/index/translation cause. |
| Guest return context | The recorded guest LR is 0x7002fdd67c. |
| Static call-site check | Decoding only LR minus four in the hash-verified image identifies a direct BL targeting 0x7002fdec10. |
| Independent caller consistency | The call site lies in the guest-symbol interval starting f_7002fdbe0c, and native stack frame 11 resolves to the same symbol. |

This supports the pair **f_7002fdbe0c → f_7002fdec10** in the observed crash context: native stack, stored guest
return address, direct instruction target and version-bound image agree. It does not recover the precise guest
instruction corresponding to the optimized native fault, provide a complete guest stack walk, or assign a
semantic name to either function. Compiler inlining/splitting and the freshness of stored guest registers must
still be considered before claiming a full guest execution history.

Local outputs: symbolized-crash.txt, native-symbol.json, native-fault-disassembly.txt and
guest-call-correlation.json under lab/reports/W31-crash-triage/.

## Single-attempt diagnostic, not a baseline gate

A fresh host directory received copies of the same two binaries and a copied pre-battle seed. The recorded
input script was reused unchanged, with a 30-second requested window limit, monitor 2, dummy audio and a
70-second owned-process safety bound. The retrying run_auto.sh wrapper was not used.

- One child, exit code 0; no FATAL or host exception in that child's log.
- Elapsed process/log-observation interval: 32.884 seconds. Last logged frame: 725.
- Copied executable/DLL hashes match the original failed run's artifacts.
- Original source-save manifest is unchanged. No game process remained at the post-run check.
- Artifacts: lab/reports/W31-crash-triage/repro-2c0b6b48/receipt.json and run.log.

**The historical failure was not reproduced in this single short attempt.** This does not establish stability,
first-battle completion, a causal relationship to memory pressure, or a fix. No new window-gate record was
manufactured for this diagnostic; run_id=e5b2041956 remains FAIL.

## Remaining investigation

The relevant functions are now concrete instead of anonymous crash offsets. Root cause still requires a
captured failing state that distinguishes a bad base pointer, bad index/lifetime, or translation/runtime defect.
Do not add a null guard, label this the previously hypothesized rare crash, or widen deferred crash work from
this metadata alone. Any future diagnostic instrumentation needs a fresh build of the actual tested backend.
Any actual Ghidra/private-function step remains separate from the W30 synthetic-only helper's scope.

[W32](windows-fault-context-2026-10-18.md) subsequently added native context capture and reporter safety, with
fresh Vulkan evidence. The W31 historical binaries remain under the repro-2c0b6b48/host/ archive above; use those
for this old crash instead of assuming the rebuilt host-vk-auto still has its old hashes. W32 does not clear this
failure or claim its game-side cause.
