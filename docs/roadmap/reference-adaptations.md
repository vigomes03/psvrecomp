# Reference adaptations and future troubleshooting

## Scope and status

The user selected these useful adaptations for the roadmap after the
[source study](../reference-study-letsgo-udpr.md). All REF items below are **open**: scope selection is not
implementation, integration or test evidence. These are supporting deliverables within the existing tracks,
not a new execution track or replacement phase numbering.

Do not expand the current B exit conditions, reopen B-01/B-02 retroactively, or make every reference idea a
prerequisite for the custom platform. Preserve the B -> R -> C order and the separate A track. Promote one bounded
implementation card when its owner task needs it. Existing capabilities should be extended or validated, not rebuilt.

## Selected adaptations

| ID | Owner / consumers | Priority and trigger | Deliverable |
|---|---|---|---|
| REF-01 | A-02; supports B-03 scenarios | Near-term test reliability | Scripted-input isolation and explicit scenario checkpoints |
| REF-02 | A-01; supports B-02 provenance | Near-term build reliability | Generated-DLL recipe identity and stale-artifact rejection |
| REF-03 | A-02 follow-up; supports B-04 recovery | After the save boundary and baseline policy are established | Opt-in verified post-save checkpoints with bounded retention |
| REF-04 | R-01; supports R-03 | At the next focused scene investigation | First-entry/caller metadata and baseline-versus-event comparison |
| REF-05 | L-08; supports A-01 automation | When promoting pipeline orchestration work | Gate-backed resumable stages, one writer and explicit failure states |
| REF-06 | R-02; supports R-04 | After observing the relevant archive/index boundary | Read-only resource/dependency inventory and missing-reference report |

### REF-01 — Input isolation and scenario checkpoints

- [ ] Add an explicit automation mode excluding physical keyboard/gamepad/mouse/stick input from the guest while
  retaining window/quit management; record seed/build identity, timeline and expected semantic checkpoints.

**Reference:** Let's Go `runtime/hle/input.c` and `tools/repro.sh`; study section 1.
**Acceptance:** injected physical input does not alter scripted guest input; normal manual controls remain available;
a copied-save scenario reaches its declared checkpoints and leaves the source unchanged. Frame-based replay alone
must not stand in for handling asynchronous loading or a modal tutorial. No turbo/60 fps acceptance shortcut.

### REF-02 — Generated game DLL identity

- [ ] Bind the generated objects/DLL to the generator, relevant CPU/SIMD headers, compile flags, toolchain identity
  and original module ids; enforce compatibility in the launcher/runtime as well as the verification flow.

**Reference:** Let's Go `Makefile`, `runtime/gamelib.h` and `runtime/gamelib.c`; study section 2.
**Acceptance:** a stale DLL with matching original NSO ids and ABI number is rejected; changing a recipe input
invalidates the affected outputs; unchanged inputs permit reuse. Retain our multi-module loader and existing
runtime-source/NSO checks. This extends provenance rather than erasing prior B-02 evidence.

### REF-03 — Verified save checkpoints

- [ ] Offer explicit opt-in checkpoints after an observed save-completion boundary, retaining the known-good
  pre-run backup and publishing only verified checkpoint directories/manifests.

**Reference:** uDPR `PcPlatform/PcFs.cs` and `PcPlatform/PcSaveCheckpoint.cs`; study section 3.
**Acceptance:** hashes detect an interrupted checkpoint copy; incomplete publication is not listed as recoverable;
restore is refused under a live owner; stale owner markers are handled using PID/start-time identity; retention
limits are exercised; the actual game loads a restored test copy. Paths remain inside the selected project data
root and original saves remain untouched. No claim of atomic Commit or power-loss durability from backups alone.
This is a follow-up convenience/safety layer, not a newly added prerequisite to the baseline backup policy.

### REF-04 — Event-focused function profiling

- [ ] Extend our existing profiler with bounded first-entry/caller information and compare matched baseline/event
  windows before introducing a more general guest-hook registry.

**Reference:** Let's Go `runtime/fnprof.c`, `tools/fncompare.py` and, only if necessary, `runtime/fnhook.c`;
study section 4.
**Acceptance:** a synthetic known call sequence validates the metadata; a versioned standing/entering/leaving
comparison yields reviewed candidates and caller observations. Use our real module layout, not Let's Go bases or
address maps. Candidate differences are not automatically a scene loader or a complete causal call graph.
Raw profiles, guest memory and generated code stay private. General hooks require a separate bounded card if needed.

### REF-05 — Resumable verified pipeline stages

- [ ] Add a queue with input/recipe/output manifests, per-stage logs and explicit pending/running/failed/verified
  states, preserving single-writer ownership and bounded attempts.

**Reference:** uDPR `setup/setup.py`; study section 5.
**Acceptance:** failed or denied commands cannot advance the queue; model prose/exit zero cannot replace a gate;
stale or missing artifacts invalidate resume; incompatible stage changes stop safely; a dry run writes nothing.
An approval denial stops that operation for review, not repeated alternate wrappers/paths or disabled safeguards.
Respect measured available RAM/VRAM and unload workers before game runs. Safe stage reruns and resource admission
need their own tests; the upstream timestamp/version state and installed-RAM check are not sufficient substitutes.

### REF-06 — Resource identity and dependency audit

- [ ] Inventory the minimum selected archive/scene resources read-only, preserving entry identity, dependencies,
  observed requests, parse errors and unknown relationships in a versioned report.

**Reference:** uDPR `setup/stages/bundle_containers.py` and `Assets/Editor/BdspProbe/BdspLoaderProbe.cs`;
study section 6.
**Acceptance:** malformed synthetic inputs are rejected; parser results correlate with actual requests; resumable
scans reject changed input archives/parser identities; missing references are reported rather than silently guessed.
Use this as a design pattern only: Unity GUIDs, AssetBundles and reflection are not our archive format or loader.
An outer RomFS override does not establish replacement of a resource inside `arc/data.trpfs`.

## Troubleshooting reference index

Consult these sources when the named problem actually appears. This table is a reference library, not a queue
of features to import or evidence that those sources solve the problem in our game.

| Problem / investigation trigger | Where to look locally | Existing owner / limits |
|---|---|---|
| Scripted scenario changes while the user touches a controller | Let's Go `runtime/hle/input.c`, `tools/repro.sh` | REF-01 / A-02; isolate physical input and check actual UI state |
| Runtime and generated DLL disagree after a tool/header change | Let's Go `Makefile`, `runtime/gamelib.c` | REF-02 / A-01; keep original module-id validation too |
| Recoverable save history or restore under a running game | uDPR `PcSaveCheckpoint.cs`, `PcFs.cs` | REF-03 / A-02; copies are not atomic transactions |
| Failure halfway through setup or a long agent-driven pipeline | uDPR `setup/setup.py` | REF-05 / L-08; gate-backed manifests, not only a done timestamp |
| Which functions appear only while entering an area? | Let's Go `runtime/fnprof.c`, `tools/fncompare.py` | REF-04 / R-01/R-03; candidates require further review |
| Missing scene resource or unknown dependency | uDPR `bundle_containers.py`, `BdspLoaderProbe.cs` | REF-06 / R-02/R-04; format-specific code is not portable |
| Reversible user-selected outer RomFS replacements | Let's Go `runtime/mods.c`, `runtime/services/fs.c` | L-04 / R-02; preserve our existing overlay and discover the inner boundary |
| Missing draw, shader, material or texture | Let's Go `runtime/nvn/vulkan/renderdoc.c`, `tools/rdc_draw.py`, `tools/rdc_skin.py` | L-05; first obtain a reproducible matched-frame defect |
| Function locations change between original game builds | Let's Go `tools/addrmap.py`, version gating in `runtime/fnhook.c` | L-02 / L-08; normalized matches are candidates, never copied addresses |
| Need a narrowly observed memory-write/counter trace | Let's Go `runtime/storetrace.c` and generator instrumentation | L-08; evaluate overhead first, no store-undo experiments by default |
| Locale-dependent checkpoint names/timestamps | uDPR `PcSaveCheckpoint.cs` invariant formatting | REF-03; metadata identity must not depend on the Windows locale |

## Snapshot and reuse rules

The source study pins Let's Go to `7c4f5aa02b13c470c55737ae3da74ff8947f534f` and uDPR to
`9e8789764c71601c2c604b692f891a3de79c2b88`. Both are local under `ref/`, ignored by the REA Git repository.
If a snapshot changes, recheck the relevant source and findings before importing an adaptation. Read the component's
license and preserve applicable notices when copying substantive code. No game content or private extracted data
enters tracked files or cloud prompts.

Do not copy the reference script that kills every executable with a matching name, its fixed C: tool paths, or
Let's Go-specific game addresses. Do not launch either setup or fetch dependencies merely to consult the source.
No baseline task is marked done by this document. D-01 (60 fps) and D-02 (rare crashes) retain their existing
resume conditions. Reference availability does not authorize their resumption.
