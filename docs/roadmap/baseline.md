# B — Reproducible baseline and save safety

**State:** B-01/B-02 have fresh evidence (run_id=69f115de36; run_id=8e0e7bcf37; run_id=bcba9b8984; run_id=bc7adfe0bc). B-04 recovery has run_id=7ea127f858 and run_id=d6946b460e; B-03 closed on current build + explicit user confirmation (run_id=38c0cfbc90; run_id=e559998a17).
See [execution notes](execution-2026-10-17.md). Historical capabilities are in the [evidence ledger](evidence.md).
Product fixes require separate bounded cards, not a blind rewrite of the runtime.

## B-01 — Headless host regression

- [x] Reproduced the headless failure (run_id=5bca0b86c4, FAIL), added a regression assertion, supplied the missing no-driver shim entry point, and reran the host gate (run_id=69f115de36); targeted checks run_id=dc8810b71b.

**Known input:** run_id=648a2fa61b records an undeclared SDL audio-driver function. Read current declarations,
null-backend headers and build selection before choosing a fix. Do not assume this is a Vulkan regression.
**Acceptance:** a fresh host gate for v4.0.0, actual output artifacts, no build error; a failing run remains visible.
**Old scope:** 1.2/1.6, 2.1-2.4/2.6, 5.1. Historical boot does not re-close these full composite scopes.

## B-02 — Versioned build and input provenance

- [x] Input/runtime build ids and bases agree; pinned inputs run_id=01d413a344, headless build run_id=69f115de36 and two frame/time-limit boots run_id=8e0e7bcf37; isolated Vulkan build/link run_id=bcba9b8984 and run_id=bc7adfe0bc. Provenance and limits are in the execution notes.

Use existing scripts/gates after inspecting their current help and implementation. Never reuse a function count
from another build. Do not open key contents or overwrite extraction/generation outputs without a scoped card.
**Acceptance:** matching input/runtime build ids, recorded build/link commands and fresh frame/time-limit gate;
base is an explicitly separate comparison, not silently required for the platform experiment.
**Old scope:** 0.1/0.2, 1.1-1.3/1.6, 2.1/2.2/2.6. Uncovered inventory/CPU/services remain in the backlog.

## B-03 — Window and route regression

- [x] Fresh current-build gate: new game run_id=38c0cfbc90 and 600 s copied save run_id=e559998a17, both on the build of run_id=240fe07924, first attempts clean, original save hash unchanged, FPS windows matching the gate threshold (see route comparison). The user explicitly confirmed first-battle completion and free map movement without observed lag, visual bugs or crashes on the same build.
- [x] Historical failure run_id=e5b2041956 (copied pre-battle, first-attempt fault) remains recorded as FAIL with its crash triage and W32/W33 follow-ups. The current build's fresh gates plus explicit user confirmation close B-03 under its acceptance; this is not retroactive repair of that old attempt and not a retroactive claim that the Poco Path transition was exercised in either automatic route.
- [x] Route comparison against E-06/E-07 updated with the two new rows; OCR-based observation and human checkpoints labelled separately.

**Acceptance:** fresh window evidence with build/input provenance (run_id=38c0cfbc90; run_id=e559998a17), semantic checkpoints separately labeled (human confirmation in manual-test-2026-10-18.md; OCR observation noted as not user approval), and the route report updated. No failures hidden by retries.

**Status: B-03 closed.** The [2026-10-18 manual session](manual-test-2026-10-18.md) on the build of
run_id=240fe07924 had an explicit user report of no visual issues/crashes, plus confirmation of the first battle,
free map movement and no perceived lag. The two fresh current-build gates above satisfy the window/route
acceptance; human checkpoints are recorded separately from automatic metric checkpoints.

**Old scope:** 4.1-4.3 observed-path regression, 6.1/6.2/6.4-6.8. General hardening remains L-05/L-07.

## B-04 — Save isolation and interruption policy

- [x] Copied-save isolation, fresh write/reload and deliberate write-boundary interruption/recovery have run_id=f933f43273, run_id=4ec8dcdc29, run_id=a9bef169e1, run_id=7ea127f858 and run_id=d6946b460e. See the [bounded recovery policy](../save-recovery-policy.md); no atomic Commit or power-loss claim.

Audit the actual game's write/rename/Commit sequence. The previous source inspection found a no-op Commit;
that alone neither establishes atomicity nor proves every game-managed save update is unsafe.
Decide whether a host transaction mechanism is required; if so, implement/test it on a bounded card.
**Acceptance:** original save remains untouched; copied-save persistence and backup restoration are demonstrated;
interruption tests use expendable data and record the achieved guarantees and remaining limitations.
A policy based on backups is not mislabeled as atomic Commit.
**Old scope:** 3.4 and the save part of phase 5. Precondition for C experiments.

## Exit

B tasks report separate outcomes. A working window route does not erase a failed headless build;
read-only study can progress independently when tools fit, but no map modification bypasses save isolation.
Next: [scene/data study](scene-study.md) or [application acceptance](application.md).
