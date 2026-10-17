# B — Reproducible baseline and save safety

**State:** open. Historical capabilities are in the [evidence ledger](evidence.md); none of the fresh tasks below
is implied by an old gate. Product fixes require separate bounded cards, not a blind rewrite of the runtime.

## B-01 — Headless host regression

- [ ] Reproduce the latest recorded headless build failure with the current source, preserve its diagnostics,
  isolate the root cause, apply only the necessary correction, and rerun the same build through the gate.

**Known input:** run_id=648a2fa61b records an undeclared SDL audio-driver function. Read current declarations,
null-backend headers and build selection before choosing a fix. Do not assume this is a Vulkan regression.
**Acceptance:** a fresh host gate for v4.0.0, actual output artifacts, no build error; a failing run remains visible.
**Old scope:** 1.2/1.6, 2.1-2.4/2.6, 5.1. Historical boot does not re-close these full composite scopes.

## B-02 — Versioned build and input provenance

- [ ] Record current v4.0.0 input build ids, generated module layout, source revision and actual artifacts; build/link
  the intended configurations and record fresh headless frame/time-limit evidence.

Use existing scripts/gates after inspecting their current help and implementation. Never reuse a function count
from another build. Do not open key contents or overwrite extraction/generation outputs without a scoped card.
**Acceptance:** matching input/runtime build ids, recorded build/link commands and fresh frame/time-limit gate;
base is an explicitly separate comparison, not silently required for the platform experiment.
**Old scope:** 0.1/0.2, 1.1-1.3/1.6, 2.1/2.2/2.6. Uncovered inventory/CPU/services remain in the backlog.

## B-03 — Window and route regression

- [ ] Run the current Vulkan build through a new-game route and a 600-second copied-save open-world route at 30 fps.

Capture first-attempt results, no FATAL/exception, FPS/frametime windows, screenshot paths and named checkpoints.
Ask the user to confirm semantic/visual checkpoints that image metrics cannot establish. Include first-battle and
Poco Path transitions when the copied saves/routes support them; do not claim random exploration.
**Acceptance:** fresh window evidence with build/input provenance, semantic checkpoints separately labeled,
and a route report comparing regressions against E-06/E-07. Never hide failures with retries.
**Old scope:** 4.1-4.3 observed-path regression, 6.1/6.2/6.4-6.8. General hardening remains L-05/L-07.

## B-04 — Save isolation and interruption policy

- [ ] Document and demonstrate copied-save isolation, backup/restore and failure recovery before any modded run.

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
