# L — Hardening, future scope and explicit deferrals

These items preserve the remaining scope without making every study idea a prerequisite for a platform.
All are open. **Later proposal** is a scheduling recommendation, not a statement that the user deferred it.
Promote one bounded card when it blocks the chosen slice or the user selects it.

## Hardening and broader study

| ID | State | Scope / old IDs | Acceptance before closure |
|---|---|---|---|
| L-01 | Later proposal | Full executable/service/NVN inventories and Eden SVC/IPC comparison; 0.2/0.4, 2.7 | Version-tagged reproducible lists and actual paired traces; conditional Zelda dump ownership remains unresolved |
| L-02 | Open coverage debt | Actual-game integer samples, exhaustive SIMD semantics, jump-table fallback report, original-word patch guards; 1.4/1.5/1.7/1.8 | Defined corpus/denominators and zero unexplained divergences, versioned report and guard rejection test; retain E-04/E-05 sample evidence |
| L-03 | Open coverage debt | Synchronization stress, FIFO, SVC and offline IPC semantics; 2.3/2.4/2.5 | Real contention/timeout/cancellation tests and observed service coverage; boot alone is not enough |
| L-04 | Later proposal | Runtime representation/base-update layering and storage concurrency/latency; 3.1/3.2/3.3 | Explain actual prebuilt RomFS vs runtime layering, test the selected contract and measure latency; do not implement unused layering for its own sake |
| L-05 | Open coverage debt | Full NVN feature inventory, offline shader corpus/fuzz/SPIR-V, cache reload/invalidation, VRAM lifetime/budget, RenderDoc; 4.1-4.7 | Corpus and unsupported list, real validation/cache tests, budget/leak measurements and documented capture; visual fixes are retained, not redone |
| L-06 | Later proposal | Actual video path (inventory mentions Bink), clock/persistence/day-night, local account/applet/dock; 5.3/5.4/5.5 plus unexercised audio/input paths | Test the actual selected formats/services; no invented MP4/USM requirement or 1:1 day/night clock assumption |
| L-07 | Open coverage debt | Random exploration, area/thread profiles, cold-cache stutters and display pacing; 6.3/6.4/6.5/6.6/6.8 | Named routes/areas, genuine failures, cold/warm metrics and measured monitor pacing; B-03 is only the baseline route |
| L-08 | Later proposal | Memory search/poke, full capture/metric suite, complete names/snapshot/Ghidra bridge; 7.1-7.9 beyond R | Demonstrated tools used on real evidence, reproducible lookup and reviewed names; no tools added merely because LAS has them |
| L-09 | Later proposal | Widescreen/ultrawide, draw distance, free camera/stats, save editor/randomizer/data mods; 8.4/8.6/8.7/8.8 | Separate design, dependencies and acceptance per feature; general warp depends on known scene semantics |
| L-10 | Later proposal | Full engine/job/heaps, world grid/LOD, all formats/render passes, battle/AI/Terastal/spawn/day-night, complete middleware and Zelda comparison; 9.1-9.7 beyond R | Reviewed descriptive notes with actual sources/build ids and bounded questions; discovered facts vs hypotheses clearly separated |
| L-11 | Later proposal | Independent scene registration/warp, JSON generator/exporters, validation, open-world cell; 10.5.1-10.5.3, 10.6.1-10.6.3, 10.7.1/10.7.2 | C slice first, then separate evidence for registration, generated formats and unload/reload/LOD neighbors; no assumption of a regular grid |

## Reference-backed follow-ups and future troubleshooting

The canonical [REF-01 through REF-06 checklist](reference-adaptations.md) is planned scope, not a second set of
L checkboxes. Consult its problem-to-reference index before investigating a similar issue from scratch.

| Existing owner | Reference retained for a matching problem | Promotion rule |
|---|---|---|
| L-04 | Let's Go mod selection and outer RomFS overrides | Reuse our overlay; investigate inner-resource boundaries before promising a map replacement |
| L-05 | Let's Go targeted RenderDoc capture and draw/skin inspection helpers | A reproduced graphics defect and a matched-frame capture justify a bounded card |
| L-08 / A-01 | uDPR stage state/logging, adapted as REF-05 | Gate-backed resume and invalidation tests; one writer and explicit command authorization |
| L-08 / R-01 | Let's Go bounded hooks and store tracing beyond REF-04 | Extend profiling first; add invasive instrumentation only when the selected question needs it |
| L-02 / L-08 | Let's Go cross-build normalized instruction matching | Candidate discovery only; validate build identity and semantics before accepting a mapped function |

No upstream tool or game-specific address is imported automatically. Keep deferred performance/crash work separate.

## Existing user deferrals

| ID | State | Scope | Resume condition |
|---|---|---|---|
| D-01 | User-deferred | 60 fps / PVR_GAME60; old 6.9 and 8.3 | User explicitly requests it; then test time step, physics, animation and cutscenes, not just limiter rate |
| D-02 | User-deferred | Rare battle-loading and locker-room crashes | Existing decision: after app work, or sooner if reproducible/recurrent or blocking the selected slice |

For D-02, the archived index contains the original save/log references. Battle-loading race and corruption
mechanisms remain hypotheses, distinct from the recorded deterministic `7000cedb00` dispatch repair.
Do not diagnose a map-id error from an unordered_map crash. A new deterministic blocker must be surfaced,
not ignored merely because rare crashes were deferred.

## Evidence debt versus feature debt

Code found but not tested is not necessarily absent code. Choose a validation card before a rewrite.
Conversely a historic game run does not mean each service, shader or data format is fully covered.
Use the [ledger](evidence.md) and [archived audit](archive/2026-10-17/status-audit-2026-10-17.md)
for provenance, not archived priority text.
