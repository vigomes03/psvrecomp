---
name: switch-static-recompilation
description: Extract and recompile Switch titles with verified gates.
version: 1.0.0
author: [USER] (project-contributor), Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [switch, arm64, recompilation, hactool, vulkan, psvrecomp]
    related_skills: [rea-local-lab]
---

# Switch static recompilation

Use this skill for the PSV Recomp pipeline: a user-owned Switch title is
extracted locally, its ARM64 code is lifted to C, compiled to a native DLL, and
executed through the project runtime and NVN-to-Vulkan backend. The workspace
is private and local-only; `CLAUDE.md` remains the controlling authority.

## When to Use

- Extracting a base title or update from user-owned media.
- Regenerating C and native object files from an extracted v4.0.0 ExeFS.
- Building, linking, booting, testing, launching, or debugging PSV Recomp.
- Investigating runtime, input, save, audio, rendering, shader, or performance
  behavior in the static recompilation pipeline.

Do not use for unrelated Switch emulation, game redistribution, or downloading
ROMs, keys, firmware, or game assets.

## Privacy and Proof Rules

- Keep ROMs in `roms/`, keys in `keys/`, extracted content in `dumps/`, and
  generated/private analysis artifacts in `lab/`. They are ignored and must
  never be committed or copied to project documentation.
- Use only the user's own dumps and keys. Do not fetch copyrighted game content
  or keys from the network.
- A build, link, boot, window, SIMD, or gameplay claim is accepted only after
  the appropriate `tools/verify/gates.py run ...` command records a real
  `run_id`.
- Keep the manual save in `lab/host-vk/save` separate from pipeline saves.
  Automated runs use their isolated `save_auto` directory and a `SAVE_SEED`.

## Shortcuts in scripts/

| Command | Purpose |
|---|---|
| `scripts\extract_base.cmd` | Extract the base XCI into `dumps/base/`. |
| `scripts\extract_update_v400.cmd` | Apply the v4.0.0 update into `dumps/v400/`. |
| `scripts\recompile_v400.cmd` | Generate C and compile v4.0.0 modules into `lab/gen-v400/`. |
| `scripts\build_and_test_v400.cmd` | Build and boot-test an isolated Vulkan host. |
| `scripts\launch_game.cmd` | Delegate to the canonical manual-play launcher. |

Every scripts/ shortcut provides `--help`, checks prerequisites, and must preserve
its nonzero child exit code. Windows `.cmd` files use CRLF endings.

## Procedure

1. **Inspect before writing.** Read `CLAUDE.md`, the relevant roadmap page, and
   the source/launcher being changed. Confirm no `pvhost.exe` instance owns the
   target output or save. Completion criterion: the changed path, build target,
   and validation gate are known.
2. **Extract without disclosure.** Use the scripts/ extraction shortcuts. Let their
   private logs remain outside Git; do not print or preserve key-bearing output.
   Completion criterion: the expected extracted layout exists and the dumps gate
   passes for the selected version.
3. **Generate and compile.** Use `scripts\recompile_v400.cmd` for full regeneration or
   the canonical recomp scripts for targeted changes. Completion criterion: all
   expected object directories are produced without ignored error logs.
4. **Build and link in isolation.** Use an isolated host directory for automatic
   tests, never the user's manual-play `lab/host-vk`. Build the Vulkan host with
   the `vulkan` backend explicitly; the default null backend does not open a
   game window. Completion criterion: the host and game DLL are produced by the
   current build, not reused artifacts.
5. **Run the matching gate.** Use the smallest relevant gate, then repeat
   nondeterministic boot/crash tests enough times to establish a pattern. For
   window tests, use scripted input and a seeded copy of a save. Completion
   criterion: the gate writes a passing `run_id` and the artifact/log checks
   match the claim.
6. **Protect the user session.** Manual play uses `psvrecomp/recomp/run_window.cmd`
   with sound and monitor 2. Before destructive or diagnostic runs, keep the
   user's save backed up and state if a test will open a window or alter visuals.
   Completion criterion: manual save, settings, and running game process remain
   untouched unless the user explicitly requested otherwise.
7. **Document and commit the verified batch.** Update `psvrecomp/README.md` and
   factual logs as needed. Roadmap changes are drafted with [USER] rather than
   rewritten unilaterally. Completion criterion: staged lint passes and the
   commit contains no private, generated, or laboratory content.

## Runtime and Graphics Rules

- Implement NVN entry points as `NVN(name) { ... }` in a source file compiled by
  the host build. A standalone C function is neither registered nor proof of a
  runtime implementation.
- Diagnose rendering from real logs and captures: establish whether a pass,
  shader, texture, or draw is missing before editing the translator.
- Preserve the MSL path byte-for-byte when changing GLSL-only translation logic.
  Use an explicit GLSL branch rather than modifying shared emitted text.
- Performance priority is correct game speed, then stable 30 fps, then
  smoothness, then fidelity. Do not resume 60 fps exploration without an
  explicit user request.
- A window capture or shader A/B is only evidence when the same scene and
  controlled input/save are used on both sides.

## Gate isolation and save recovery

- `gates.py run host --version v400 --backend vulkan` and the corresponding `link` gate target
  `lab/host-vk-auto`; the null backend keeps `lab/host-v400`. Window acceptance uses the isolated Vulkan host.
- A source save and an expendable sandbox must be disjoint; reject equal/nested paths and missing inputs before
  deleting anything. Verify the staged copy and record source hashes before/after the run.
- Demonstrate backup restoration on expendable copies. Do not call a backup policy an atomic guest Commit.
- A null-host build cannot validate Vulkan instrumentation. Require matching output hash and current runtime/header
  source manifests before window runs; retain stale-binary rejection as evidence.
- A print-mode coding agent must not promise to resume its own background test after exiting. The parent must own
  a tracked continuation, inspect the actual result and verify which binary/source version was exercised.
- Headless shims must track SDL entry points used even by logging paths; add a no-device assertion and rerun
  the shim and real host gates instead of hiding the diagnostic call.

## Pitfalls

- `build_host.sh <out>` without `vulkan` builds the null backend.
- A failed build can leave an old executable that makes a later run appear to
  test new code. Verify the current build output before treating the run as
  evidence.
- Pipeline runs are intentionally silent; manual `run_window.cmd` sessions have
  sound. Do not change the manual launcher to dummy audio.
- New performance improvements can expose races. Repeat the same repro and
  classify each crash by its first fatal or device-fault line.
- Never declare a visual defect fixed from a build or boot gate alone; require a
  same-scene render measurement or a user-confirmed manual observation.

## Crash-metadata triage

- Bind the executed host/DLL hashes to the failed run before symbolizing. Check both the nearest symbol and
  the next text-symbol boundary; a stale binary or an unbounded lookup invalidates the function attribution.
- Use the existing recomp/venv interpreter for LZ4/Capstone tools. Do not install packages globally just because
  the desktop interpreter lacks the project dependencies. Hash-compare a reused flat image with Nso.image.
- Correlate a stored guest LR minus four with the actual decoded direct target and the next native frame before
  naming a caller/callee pair. Keep native/guest metadata distinct; this does not identify the optimized guest
  fault instruction, prove register freshness, or assign engine semantics to anonymous symbols.
- Keep short diagnostic replays single-attempt with copied binaries/settings/saves and retained logs. A clean
  short run does not erase a prior failing gate. Never replace a missing reproduction with a speculative null guard.

- For Windows fault diagnosis, emit the supplied native CONTEXT before any best-effort stack read or terminal
  report. Test actual read/write/execute exceptions through the production filter, plus a silent normal path and
  hook-removal control; helper presence alone does not prove integration.
- Do not trust MEM_COMMIT as proof that saved RSP is readable. Require a full-size safe same-process copy before
  using its stack-top heuristic, and keep real NOACCESS/GUARD/cross-page regression controls. A reporter fix is not
  a fix for the original game fault; rebuild the tested backend after instrumentation changes.

- For scoped Ghidra work, validate on an ABI-correct owned fixture first. Treat compiled-symbol intervals as
  candidate bounds, not recovered canonical functions. Record actual database counts; an expected count is not
  a measurement. Keep broad analysis off and preserve private pseudocode only under ignored lab/.
- Entry-based disassembly may miss a runtime-observed interior call. Seed only the verified site within its
  budget, and retain the separate entry-flow flag; explicit seeding does not prove reachability or source fidelity.
  Keep full private failures local because executor exceptions can contain native logs.

## Verification

- Run `python tools/verify/gates.py run <gate>` for the actual claim.
- Run `python tools/verify/gates.py lint --staged` before every commit.
- Check `git status --short` and `git diff --cached --check` before committing.
- Verify that `roms/`, `keys/`, `dumps/`, and `lab/` are absent from staged
  content, except the intentional `roms/.gitkeep` marker.
