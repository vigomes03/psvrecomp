# PSV Recomp roadmap — evidence-led revision

**Revision:** 2026-10-17. **Target:** Pokemon Violet v4.0.0. **Gameplay target:** 30 fps at correct speed.
Personal, local study only. No game content, keys, generated game code or RE output is distributed.

This is the only active roadmap. The previous phase pages and audit were removed from the active directory and
preserved in a [dated archive](archive/README.md). Runtime code and machine-generated evidence were not changed.

## Read the state correctly

The project is beyond first boot: there is recorded native gameplay, rendering and a ten-minute route.
We do not need to rebuild those milestones from scratch. We need a fresh baseline, scoped acceptance for the app,
and a focused study path for the custom platform. Historical results are not current-source certification.

| State | Meaning |
|---|---|
| Established, historical | A gate covers this narrow result for the recorded build; see the evidence ledger |
| Observed | Source or a recorded manual/run_auto observation exists; not equivalent to full acceptance |
| Open | A named deliverable or its validation is still needed |
| User-deferred | Explicit prior user decision; no automatic resumption |
| Later proposal | Retained scope, not a newly approved user deferral |

A checkbox covers exactly its wording. New tasks are open until their acceptance evidence exists.
No percentage is calculated from unequal tasks. No runtime experiment was performed for this rewrite.

## What already exists

| Capability | Evidence and boundary |
|---|---|
| v4.0.0 extracted inputs | Established, historical: run_id=131ff828b2 checks pinned exefs and nonempty romfs under `dumps/v400/` |
| Recompiled DLL and headless frame path | Established, historical: run_id=7adc0390c2 (v4.0.0); run_id=db35401e31 (base). Not exhaustive CPU/kernel coverage |
| SIMD semantic sample | Established, historical: run_id=782956f97a, 20,000 encodings / 159,968 cases; not exhaustive semantics |
| Exclusive-pair sample | Established, historical: run_id=6efc28c218, five codegen checks and 200 semantic cases |
| Rendered new-game progression | Established, historical: run_id=312d34de1a; image metrics and scene changes, not semantic recognition of every screen |
| Ten-minute open-world route | Established, historical: run_id=c6a80b10d8, 17,227 frames / 600 seconds; final measured windows 28.9 fps, not free exploration |
| Audible audio, keyboard, character naming, save/load | Recorded user observations in the [pipeline log](../pipeline-log.md), 2026-10-15/16; not complete hardware/service coverage |
| Terrain, vegetation, sky/fog fixes and GPU optimizations | Recorded comparisons/experiments in the pipeline log, 2026-10-16; retain them as assets, not new pending reimplementations |
| Overlay, ini, safe start, profiling and crash diagnostics | Code and recorded observations exist; acceptance gaps are split out below |

Full provenance and rejected overclaims: [evidence ledger](evidence.md).

## Execution plan

| Track | Purpose | Current status | Exit condition |
|---|---|---|---|
| [B — Baseline and safety](baseline.md) | Establish reproducible current builds/routes and protect saves | B-01/B-02 fresh evidence; B-03 closed (new game run_id=38c0cfbc90; 600 s copied save run_id=e559998a17; human checkpoint in manual-test-2026-10-18.md); B-04 recovery run_id=7ea127f858 and run_id=d6946b460e | B-01 through B-04 have evidence |
| [A — Application](application.md) | Finish launcher and validate existing settings/input | Partial implementation, open acceptance | A-01 through A-04 have evidence |
| [R — Scene and data study](scene-study.md) | Trace one small scene and understand only its required resources | Open | R-01 through R-04 produce reviewed evidence and a safe override decision |
| [C — Custom platform](custom-platform.md) | Reversible replacement of a small area with geometry, collision and entry | Not started; depends on B and R | C-01 through C-04 are demonstrated |
| [L — Hardening and later work](backlog.md) | Preserve coverage gaps, optional features and explicit deferrals | Outside the first platform slice | Promote a bounded item only when needed/agreed |

**Order:** B first. After B, prioritize R → C for the platform experiment; A remains a separate app track.
B-02/B-03 gameplay baseline and B-04 save isolation/recovery policy precede mod execution; read-only R research
can start after the relevant tools are available. Starting a later experiment does not erase a failed baseline task.
This is a planning order, not evidence that implementation has begun or a new approval to resume deferred features.

## Selected reference adaptations

The user selected useful ideas from Let's Go Recomp and uDPR for planned adaptation, not wholesale code import.
[REF-01 through REF-06 and the troubleshooting index](reference-adaptations.md) assign each deliverable to an
existing owner: A-01/A-02 for input/DLL/checkpoints, R-01/R-02 for profiling/resource inventory, and L-08 for
resumable pipeline stages. The [source study](../reference-study-letsgo-udpr.md) records pinned snapshots and caveats.

These items remain open. They do not add blanket prerequisites to B, replace our existing runtime, reopen prior
B-01/B-02 acceptance, or resume D-01/D-02. Consult the problem-to-reference index when a matching issue appears.

## Relationship to the previous phases

Historical phase numbers 0-10 retain their meanings. B/A/R/C/L are execution-track IDs, not replacement phase numbers.
Old work cards and evidence IDs remain valid identifiers; archived checklists no longer drive the queue.

| Old phase | Preserved result | Remaining work now owned by |
|---|---|---|
| 0 — Acquisition | Extracted inputs and inventory notes | B-01/B-02 provenance, R-01 game-analysis entry, L-01 reference coverage |
| 1 — Recompiler | Historical DLL path and sampled tests | B-01/B-02 current baseline; L-02 CPU/jump-table/patch coverage |
| 2 — Runtime | Historical boot/frame path | B-01; L-03 synchronization/services |
| 3 — Files | Storage reads and reported persistence | B-04 save safety; R-02 archive/trace; L-04 latency/layering |
| 4 — Graphics | Rendered scenes and recorded fixes | B-03 regression; A-03 settings; L-05 graphics hardening |
| 5 — Systems | Reported audio/input/naming | A-02/A-04; L-06 video/account/time coverage |
| 6 — Playable | Historical scripted ten-minute route | B-03 route; L-07 broader performance/stability; D-02 rare crashes |
| 7 — Tools | Diagnostic code and generic RE harness | R-01/R-04; A-04 crash notice; L-08 extended tools |
| 8 — App | Overlay/ini/safe-start observations | A-01 through A-04; L-09 extensions; D-01 60 fps |
| 9 — Study | Diagnostic discoveries, not a full engine study | R-01 through R-04; L-10 broader AAA study |
| 10 — Map | Exploratory plan | C-01 through C-04; L-11 new scene/authoring/open world |

Detailed old-task mapping is included in each track and in the [archive guide](archive/README.md).

## First action and constraints

**Current execution:** B track is closed as evidence: B-01/B-02 fresh, B-03 closed (new game run_id=38c0cfbc90; 600 s copied save run_id=e559998a17; human checkpoints), B-04 bounded recovery. Read-only R investigation may advance independently; no deferred items auto-resumed. See [execution notes](execution-2026-10-17.md).
Failed reproductions remain in the ledger; do not erase them or promote metric gates to visual acceptance.

Keep 60 fps disabled and rare nondeterministic crashes under prior user deferrals. Escalate a crash if it becomes
repeatable or blocks the chosen slice. Every implementation card has one owner, exact output paths, a bounded
acceptance test and real evidence; follow [repository rules](../../CLAUDE.md).
