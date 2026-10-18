# Reference study: Let's Go Recomp and uDPR

## Scope and evidence

Static source review of the downloaded snapshots, compared with the current REA working tree based on
`dede06c` plus its existing uncommitted changes. No reference setup, dependency installer, build or game was run.
No runtime changes were made for this study. Recommendations below are proposed adaptations, not accepted features.

| Reference | Pinned commit | Relevant approach |
|---|---|---|
| `ref/letsgo-recomp` | `7c4f5aa02b13c470c55737ae3da74ff8947f534f` | ARM64-to-C static recompilation and a Switch host runtime |
| `ref/uDPR` | `9e8789764c71601c2c604b692f891a3de79c2b88` | Unity/C# reconstruction of Brilliant Diamond from user-supplied inputs |

A same-relative-path comparison of Let's Go runtime `.c`, `.cpp` and `.h` files found 19 byte-identical files,
36 differing files and 28 files without a same-path counterpart in our runtime. These are file-level comparisons,
not feature counts: a differently named capability may already exist here. Inventory: ignored
`lab/reports/reference-comparison.json`. Our native runtime and Let's Go describe a LAS-derived lineage;
uDPR is a separate managed-engine approach, not a replacement for our ARM64 pipeline.

**Roadmap follow-up:** the user selected the prudent adaptations for planning. The canonical task IDs, owners,
acceptance criteria and future troubleshooting index are in [reference adaptations](roadmap/reference-adaptations.md).
This source study remains the rationale, not a separate task tracker or implementation acceptance record.

## Recommended order

1. Isolate physical input during scripted tests and add semantic checkpoints to scenario records.
2. Extend provenance to the generated game DLL, its generator/header inputs and compilation flags.
3. Add explicit, verified save checkpoints after an observed save boundary, with safe restore ownership checks.
4. Extend the existing function profiler and compare matched baseline/event runs before adding general hooks.
5. Adopt resumable, versioned pipeline stages backed by our gate records and artifact manifests.
6. Build a scene-resource inventory and missing-dependency report when the actual inner archive boundary is known.

These priorities reduce the current debugging feedback loop before adding graphics features or more subsystems.

## 1. Scripted input isolation and reproducible scenarios

**Reference:** `ref/letsgo-recomp/runtime/hle/input.c:69-86`,
`ref/letsgo-recomp/runtime/hle/input.c:155-164`,
`ref/letsgo-recomp/runtime/hle/input.c:414-449`, `ref/letsgo-recomp/tools/repro.sh:25-43`.

Let's Go blocks physical controller polling and host input events in scripted runs. Its input timeline uses
presented frame numbers, and its reproduction script chooses explicit screenshot frames and a copied save.

**REA comparison:** `psvrecomp/runtime/hle/input.c:39-62` uses milliseconds, and `fill_state` combines scripted
buttons with physical host buttons. The native game can therefore receive unrelated physical input during a
scripted test. Our separate settings and source-save manifests are useful protections that should remain.

**Adaptation:** a test-only input-isolation option covering keyboard, gamepad, mouse and sticks; preserve quit/window
management controls. Record the save hash, tested binary hashes, timeline and expected screen checkpoints per scenario.
Use explicit modal acknowledgments/checkpoints rather than assuming a fixed button sequence reached a menu.
Frame-based replay is useful, but is not proof of determinism across asynchronous loading or different caches.
Do not adopt the reference's turbo timing for 30 fps acceptance.

**Proposed acceptance:** injected physical events cannot change the guest test input; manual play still receives
normal input; the selected route reaches independently checked menu/state checkpoints without changing the source save.

## 2. Generated-code identity, not just the original game's version

**Reference:** `ref/letsgo-recomp/Makefile:103-128`,
`ref/letsgo-recomp/runtime/gamelib.c:19-28`, `ref/letsgo-recomp/runtime/gamelib.c:58-74`.

The reference hashes generator files, supporting headers and generation/compiler flags into `GAMELIB_ID`.
It checks a sidecar before loading ordinary candidates, and checks the exported ABI/id after loading.
The sidecar is an operational compatibility signal, not a security signature or proof of safe DLL initialization.

**REA comparison:** `psvrecomp/runtime/pvgame.h:17-35`, `psvrecomp/runtime/main.c:18-28`,
`psvrecomp/runtime/loader.c:57-61`, `psvrecomp/recomp/layout.py:30-36`.
We already have a DLL interface, ABI validation, per-module original NSO build-id checks and a layout-derived id.
The startup path inspected logs the DLL id rather than comparing it with a generator/header/flags fingerprint.
The newer gate-side runtime-source manifest is not the same thing as a generated-code identity enforced at startup.

**Adaptation:** keep our multi-module table and module build-id checks; add a distinct recipe fingerprint for the
lifted objects/DLL. Include generator/lifter/pass inputs, relevant CPU/SIMD headers, compile flags and toolchain
identity. Bind that fingerprint to the link record and launcher; do not replace all of our loader with theirs.

**Proposed acceptance:** a stale game DLL is rejected even when the original NSO build ids and ABI number match;
unchanged inputs permit reuse, and changing a generation/header/flag input invalidates the affected artifacts.

## 3. Commit checkpoints and safe recovery

**Reference:** `ref/uDPR/Assets/Scripts/_Ours/PcPlatform/PcFs.cs:117-130`,
`ref/uDPR/Assets/Scripts/_Ours/PcPlatform/PcSaveCheckpoint.cs:69-139`.

uDPR's host Commit flushes open streams and requests a checkpoint for a writable save mount. Checkpoints are
opt-in, numbered and described by metadata. A playing marker supports refusing restores while the game is active.
Snapshot exceptions are caught so a failed development backup does not fail the game's save.

**REA comparison:** copied-save isolation, verified restoration and source manifests already exist in
`tools/verify/gates.py`. `psvrecomp/runtime/services/fs.c` exposes a save-tagged Commit boundary but does not
currently turn it into an automatic post-Commit checkpoint service.

**Adaptation:** preserve a pre-run known-good backup, then optionally checkpoint an observed save completion.
Use a staging directory, file hashes and a published manifest to distinguish a valid checkpoint from an interrupted
copy. Use explicit project-contained paths and an owner/PID/start-time check, not a bare marker alone: crashes can
leave stale markers. Add retention limits, because neither numbering nor copying alone bounds disk consumption.
Avoid copying player names or unknown game structs into tracked metadata.

**Important limit:** post-Commit copies are backups, not atomic transactions, and do not automatically survive
power loss. The uDPR snapshot implementation copies directly to its target; its internal lock is not a general
cross-process transaction. Also, Let's Go still has direct `pwrite`, `fsync` and an empty Commit handler:
`ref/letsgo-recomp/runtime/services/fs.c:444-451`, `ref/letsgo-recomp/runtime/services/fs.c:575`.
Do not replace our save handling expecting that fork to supply atomic saves.

**Proposed acceptance:** verify checkpoint hashes, recover from an interrupted checkpoint publication, reject restore
under a live owned game, recover a stale owner marker safely, and load the restored copy in the actual game.

## 4. Differential profiling first, narrowly scoped guest hooks second

**Reference:** `ref/letsgo-recomp/runtime/fnprof.c:49-62`,
`ref/letsgo-recomp/runtime/fnprof.c:83-92`, `ref/letsgo-recomp/tools/fncompare.py:19-27`,
`ref/letsgo-recomp/tools/fncompare.py:61-84`.

The reference profiler stores first-entry order and the first caller's guest link register, in addition to counts.
The comparison tool subtracts baseline functions from event runs and separates common/distinct event functions.

**REA comparison:** `psvrecomp/runtime/cpu.h:64-67` already routes function entries to our profiler, passing guest
LR and x0. `psvrecomp/runtime/fnprof.c:46-54` counts entries, and `psvrecomp/runtime/fnprof.c:74-84` writes address/count
rows. Optional targeted backtraces also exist. We should extend that path, not add a second profiler unnecessarily.

**Adaptation:** collect first-entry/caller metadata in a bounded window, compare standing/entering/leaving the same
small area, then inspect a narrow candidate set. Parameterize our actual module layout: the reference tool contains
Let's Go-specific bases and generated-file assumptions. New functions or first-caller observations are candidates,
not proof of causation, a complete call graph, or the identity of a scene loader.

The larger reference hook registry (`ref/letsgo-recomp/runtime/fnhook.c:19-30`,
`ref/letsgo-recomp/runtime/fnhook.c:79-122`) allows opt-in entry wrapping and calling the original implementation.
Its version-gated registration is useful for R-01/R-02. Our `FN_ENTER` does not expose the same general hook registry.
Do not import its addresses, build remaps or Let's Go-specific game hooks. Preserve inactive-build behavior, thread
safety and ABI compatibility; validate guest memory reads against mapped ranges, not a broad address interval alone.

## 5. Resumable pipeline stages with verifiable invalidation

**Reference:** `ref/uDPR/setup/setup.py:82-94`, `ref/uDPR/setup/setup.py:153-199`.

uDPR keeps stage state, logs each subprocess and stops on nonzero exit. Versioned stages distinguish operations
that can be repeated safely from those requiring a fresh setup; verification can run again after earlier changes.

**REA comparison:** our gate runner already provides actual run ids, checks and artifact hashes, but the recent
work has depended heavily on ad hoc agent invocations and manual handoffs. A stage queue could use those records
rather than treating a model's final message or exit zero as acceptance.

**Adaptation:** stage dependencies with one writer, bounded attempts, explicit pending/running/failed/verified states,
exact command authorization and artifact-based resume. A completed timestamp/version is insufficient if inputs or
outputs changed. Keep a source/input/recipe manifest per stage and detect missing or stale artifacts.

**Cautions found in the reference:** `--plan` still writes setup configuration before its plan-only branch
(`ref/uDPR/setup/setup.py:121-145`); a new REA dry run should not do that. Its smoke step reports summary counts
without making those counts a pass/fail gate (`ref/uDPR/setup/stages/verify.py:50-61`). Keep our stricter acceptance.
The preflight's memory function measures installed RAM (`ref/uDPR/setup/stages/check.py:37-44`), not current free
headroom; do not use it as the admission check for Qwen plus another workload.

## 6. Scene-resource inventory, identity and dependency audits

**Reference:** `ref/uDPR/setup/stages/bundle_containers.py:26-91`,
`ref/uDPR/setup/stages/bundle_containers.py:123-140`,
`ref/uDPR/Assets/Editor/BdspProbe/BdspLoaderProbe.cs:71-107`.

uDPR separates metadata scanning from mapping project files, records dependencies and errors per resource, and
checkpoints scans. The loader probe records request outcomes and object/material/script problems.

**Adaptation:** for R-02/R-03/R-04, produce a versioned resource index and compare matched scene transitions.
Record archive entry identity, observed request/caller, size, dependencies, parse errors and unknown relationships.
Resume a read-only scan only when the input archive and parser identity still match. Do not decode every mesh or
texture merely to inventory metadata.

**Not portable as code:** UnityPy, Unity GUIDs, AssetBundles, C# AssetManager and scene reflection do not describe
our native title's archive format. A probe that manually initializes a manager also does not prove the natural
in-game loading sequence. There is no demonstrated TRPFS parser/writer or Scarlet/Violet collision authoring
solution in the source slices reviewed here.

## Existing overlap: do not rebuild this from scratch

The REA outer RomFS index and virtual overlay already exist at
`psvrecomp/runtime/services/fs.c:224-287` and `psvrecomp/runtime/services/fs.c:290-319`.
Let's Go's analogous path substitutes `mod_romfs_override` for our `rando_romfs_override`:
`ref/letsgo-recomp/runtime/services/fs.c:250-280`. Its `runtime/mods.c` adds a user-facing mod selection/install layer.
This is useful for organizing reversible mods, not evidence that replacing a RomFS entry replaces an inner
resource inside `arc/data.trpfs`. Establish that inner boundary before the custom-platform experiment.

Our dynamic game library, HLE registrations, reset hooks and profiler also already exist. Source presence in
another fork is not proof that we lack a capability or that it behaves better in our title.

## Additional tools worth retaining, not the next priority

- Targeted multi-frame RenderDoc capture: `ref/letsgo-recomp/runtime/nvn/vulkan/renderdoc.c:31-62`.
  Useful for a reproducible rendering defect, not for establishing archive dependencies or scene lifecycle.
- Cross-build address candidates: `ref/letsgo-recomp/tools/addrmap.py:17-55`.
  Normalized instruction matching can narrow an investigation; it does not prove function or struct equivalence.
- Store tracing: `ref/letsgo-recomp/runtime/storetrace.c:82-124` plus generator instrumentation.
  More invasive and potentially expensive than extending the existing profiler. Do not import its store-undo
  experiments or resume deferred 60 fps work as part of this study.
- The reference `ref/letsgo-recomp/tools/trace_run.sh:21` kills all processes with its executable name. Do not run/copy that behavior;
  automation here must identify its own PID, executable path and creation time.

## Suggested bounded work, not an implementation commitment

| Proposed slice | Track | First verifiable target | Reuse level |
|---|---|---|---|
| Input-isolation option and scenario metadata | B-03 / A-02 | Physical events excluded in tests, included in manual play | Adapt the mechanism |
| Full generated-DLL recipe identity | B-02 / A-01 | Reject stale DLL with unchanged NSO build ids | Adapt hashing and loader checks |
| Verified opt-in save checkpoints | B-04 / A-02 | Recover checkpoint copy/publication failures without touching the source | Adapt the design; retain our isolation helpers |
| First-entry/caller fields and event comparison | R-01 / R-03 | Matched baseline/event profiles with known synthetic call ordering | Extend our profiler |
| Gate-backed resumable queue | Pipeline / A-01 | Reject fake agent success, stale artifacts and unsafe reruns | Adapt stage-state ideas |
| Read-only archive/dependency inventory | R-02 / R-04 | Bounds-checked selected archive entries correlated with requests | Pattern only; format must be investigated here |

## Attribution and limits

Both root LICENSE files declare MIT for their own work; separate notices and third-party terms remain relevant:
`ref/letsgo-recomp/LICENSE:1-26`, `ref/letsgo-recomp/LICENSE-LASRecomp`,
`ref/uDPR/LICENSE:1-26`, `ref/uDPR/THIRD_PARTY.md:1-33`.
Before copying substantive code, retain the applicable notices and inspect the specific component's terms.
No game content, generated code, extracted assets, private dumps or keys should be copied into tracked files.

This is a targeted architectural study, not an exhaustive correctness/security audit or a portability test.
