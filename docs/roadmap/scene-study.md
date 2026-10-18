# R — Study one scene and its resources

**Goal:** explain a small scene's actual loading path and identify a justified modification point.
Do not attempt the whole engine first. No package, scene or collision format is assumed from its extension.
Use current evidence from [B](baseline.md) when running the game; read-only investigation can start independently.

## R-01 — Analysis entry and minimal tool chain

- [ ] Identify the v4.0.0 target/build id, prove REA/Ghidra can analyze the required functions, and validate the
  profiler/address-symbol workflow on a specific observed call path.

Use the local worker harness and repository rules. Record module/address, actual tool outputs and reviewed claims.
Create a names table only for confirmed discoveries. No automatic import of every subsystem is required.
**Acceptance:** a reproducible analysis entry, resource/time observations and at least one reviewed real call chain.
**Old scope:** 0.3, 7.1/7.2/7.5-7.9, narrow loader/thread portion of 9.1. Generic harness existence is not this result.

**Tooling progress (not milestone acceptance):** the installed direct-Ghidra helper now passes six synthetic
controls, including an assembler-verified BL/target/function, non-call rejection and bounded owned-JVM timeout.
See [reproducible procedure](../../tools/analysis/README.md) and the W30 evidence in
[execution notes](execution-2026-10-17.md). The synthetic controls are not an observed guest call chain.
[W31 crash correlation](crash-triage-2026-10-18.md) subsequently bound a concrete caller/callee pair using runtime
stack/return metadata, native symbols and a version-bound Capstone decode. That does not establish the required
Ghidra/private-function analysis, semantic roles or a scene-resource path; R-01 remains unchecked.

[W34 scoped real-image entry](scoped-analysis-2026-10-18.md) subsequently verified the same direct call with
Ghidra and emitted two local candidate decompilations. The caller has warnings and entry-based CFG did not reach
the observed call site; explicit seeding is not full flow/boundary recovery. Semantic roles and private-output
review remain pending. No original source reconstruction or scene-load chain is claimed.

**Selected reference adaptation:** [REF-04](reference-adaptations.md) extends the existing profiler with
first-entry/caller observations and baseline/event comparison. Prefer this bounded tool before a general hook
registry; candidate functions still need reviewed evidence for the R-01 call chain.

## R-02 — Archive/index access and read trace

- [ ] Locate the package lookup/decompression boundary, trace outer reads and determine whether an inner-resource
  trace is needed; build the minimum read-only index/parser for the selected scene.

First inspect existing filesystem/log hooks. `fsp-srv` may reveal only offsets inside a large archive.
Choose outer storage instrumentation, an inner-reader hook or package reconstruction based on observations.
Do not promise that a RomFS file replacement substitutes an inner asset hash.
**Acceptance:** version-tagged package/index relationships, bounds-checked parsing, malformed-input tests on
synthetic fixtures, and comparison of selected parser results with actual game requests. Any unknown hash/path
relationship is stated. Extracted bytes and raw reports remain private/ignored.
**Old scope:** 3.5 + package part of 9.3 + 10.1.1/10.1.3 + 10.2.1. One shared deliverable, not three parsers.

**Selected reference adaptation:** [REF-06](reference-adaptations.md) provides a read-only inventory/dependency
report pattern shared with R-04. The archive parser is specific to our observed inputs; Unity bundles/GUIDs and
an outer RomFS replacement do not establish the inner-resource format.

## R-03 — Small-scene loading experiment

- [ ] Compare standing, entering/leaving one reachable small area, and returning to it; identify the scene's
  resource set, request order and lifecycle with evidence.

Verify the selected location is actually an isolated transition; a door is not proof of an interior scene.
Use copied saves and matched conditions. Separate prefetch/cache reads from required load/unload behavior.
Add world walking/fast travel only if needed to distinguish the selected loading path.
**Acceptance:** reproducible route and trace, current build ids, observed caller/request correlation and a reviewed
note in `docs/re/` distinguishing observations from hypotheses. A generic cell grid/LOD narrative is insufficient.
**Old scope:** narrow 9.2/9.1, 10.1.2/10.1.4 and scene registration part of 10.5.1; full open-world analysis remains L-10.

## R-04 — Dependency contract and go/no-go

- [ ] Identify geometry, materials, collision, transform/entry, scripts and scene registration for the chosen area;
  decide where a reversible substitution can be made.

Study only the relevant entity/physics middleware paths. Reuse material only if its compatibility is observed,
not because it supposedly guarantees no shader changes. Do not conflate visual mesh and physics data.
**Acceptance:** reviewed dependency graph with actual references and unknowns; parser/writer contract; no-change
round-trip plan (byte-identical, or justified semantic equivalence for every required field); explicit go/no-go for C.
If no safe writer/interception path is found, report the blocker instead of emitting speculative mod files.
**Old scope:** relevant 9.3/9.6, 10.2.2/10.2.3/10.2.4 and 10.5.1. Broad middleware research remains L-10.

## Exit

A scene-load note, an archive/resource contract and a justified override strategy unlock the
[custom-platform slice](custom-platform.md). No evidence here establishes a new scene id, arbitrary warp or
open-world cell replacement. Proposed hook names from the old plan are not existing APIs.
