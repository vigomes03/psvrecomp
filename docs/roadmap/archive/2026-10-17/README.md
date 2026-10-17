# Roadmap: Pokémon Violet Recomp (PVRecomp)

> **Goal:** do with Pokémon Violet what LAS Recomp did with Zelda: **static recompilation** of the game's ARM64
> code to C, with a native runtime (fake Horizon OS + NVN→Vulkan), becoming a **Windows application
> that runs the game** from our dump. After that, understand the game from the inside and add features.
>
> **Scope:** personal study, **100% local**. Nothing leaves this machine: no remote, no upload, no release.

Technical basis: [lasrecomp-study.md](../lasrecomp-study.md) (how Zelda was done). Work rules: [CLAUDE.md](../../CLAUDE.md)
(Claude orchestrates, local models execute, everything verified).

## Phases

| # | Phase | Output (verifiable milestone) | LAS Recomp equivalent | Status |
|---|---|---|---|---|
| 0 | [Acquisition and reconnaissance](phase-0-acquisition.md) | extracted dump (base + update), executable inventory, "worth it / not worth it" decision | user's dump + `nso.py`/`analyze.py` | 🟡 v4.0.0 extraction gate run_id=131ff828b2; reconnaissance/REA/reference tasks remain partial |
| 1 | [Recompiler](phase-1-recompiler.md) | all of `main` becomes C that **compiles**; differential tests green | `tools/gen.py`, `lifter.py`, `simd_c.py` | 🟡 Historical DLL milestone; sampled SIMD run_id=782956f97a; 1.4/exhaustive 1.5/1.7 report still open; deterministic battle dispatch fix recorded |
| 2 | [Minimal runtime / headless boot](phase-2-runtime-boot.md) | the game runs `nn::init::Start` → `nnMain` and reaches the main loop **without graphics** | `loader.c`, `kernel.c`, `dispatch.c`, `ipc.c`, `services/` | 🟡 Historical M2 run_id=7adc0390c2 / run_id=db35401e31; latest headless host build failed run_id=648a2fa61b |
| 3 | [File system and data](phase-3-files.md) | the game reads the romfs (base + patch) and the `trpfs` files on its own | `services/fs.c`, `romfs_build.c` | 🟡 Observed romfs reads and manual save/load; runtime layering, latency, atomic commit and parser not established |
| 4 | [Graphics: NVN → Vulkan](phase-4-graphics.md) | **first frame**: logo / title screen rendered | `runtime/nvn/*`, `maxwell/translate.c`, `vulkan/` | 🟡 Historical rendered-scene gate run_id=312d34de1a; full shader/cache/VRAM validation open |
| 5 | [Audio, input, save, time](phase-5-systems.md) | controller works, sound plays, save writes/loads | `services/audio.c`, `hle/input.c`, `fs.c` (save) | 🟡 User observed keyboard, sound and character naming; composite hardware/service/video tests still open |
| 6 | [Playable](phase-6-playable.md) | start a new game and walk around the open map | shot.sh loop + fixes | 🟡 Historical 600 s open-world route run_id=c6a80b10d8; random exploration/current regression matrix open; rare crashes deferred |
| 7 | [RE and debug tools](phase-7-re-tools.md) | (ongoing) fnprof, `PVR_*` hooks, automatic screenshot, REA/Ghidra | `fnprof.c`, `LARECOMP_*`, `sym.py`, `shot.sh` | 🟡 Diagnostic tools partly present; game REA workflow, names and bridge still unverified |
| 8 | [The application](phase-8-application.md) | launcher, overlay menu, unlocked resolution/FPS, our own features | `ui/launcher.mm`, `menu.mm`, `hle/widescreen.c` | 🟡 Overlay/ini code and observations; launcher and complete feature acceptance pending |
| 9 | [Understanding the game (AAA study)](phase-9-aaa-study.md) | documentation of engine, formats, game systems | (does not exist in LAS: it is our study goal) | ⬜ Reviewed study deliverables open; map-oriented subset proposed, not yet executed |
| 10 | [Custom map with a platform](phase-10-custom-map.md) | an area of our own (platform + collision + spawn) loaded by the game | (does not exist in LAS: exploratory) | ⬜ Plan only; scene/format/override feasibility requires experiments |

Actual order: **0 → 1 → 2 → 3 → 4 → 5 → 6 → 8**, with **7 and 9 running in parallel** since phase 1.

## Audit status (2026-10-17)

See [the task-by-task evidence audit](status-audit-2026-10-17.md) and the dated audit at the top of each phase.
A historical gameplay milestone does not close every checklist item. Unchecked tasks can be partial, unverified,
or explicitly deferred; read the phase audit for the distinction. No build/game was rerun in this documentation audit.

**Current-health warning:** latest recorded headless host build failed at `audio.c:943`
(undeclared `SDL_GetCurrentAudioDriver`, run_id=648a2fa61b). This does not invalidate older gameplay observations,
but a fresh baseline is needed. Save Commit is a no-op (`runtime/services/fs.c:568`); persistence is not atomicity.

**Priority proposal:** revalidate the baseline; then either finish the app (8.1/8.2/8.5), or pursue the map subset
(3.5 + 9.3 package/index, 9.2/10.1 scene trace, geometry/collision/spawn, reversible override).
Keep 60 fps and rare nondeterministic crashes under the existing user deferrals. Other postponements need agreement.

## Historical status and next steps (review with [USER], 10/16/2026)

**Main target: v4.0.0** (with the update). v1.0.0 remains only as a comparison build.

Milestones: M0-M2 proven by gate. **M3-M6** have the `window` gate/manual test by [USER]; M6 includes 10 min in the open world
(run_id=c6a80b10d8). The gameplay target is **stable 30 fps, with correct speed**. Exploring 60 fps is on hold until
[USER] explicitly asks for it.

Current work order (10/16; 🟢 = real run/test; rare crashes are low priority, after the app):
1. 🟢 **Performance / 30 fps (6.6):** the game's interval 2 holds 30 fps and the correct speed. The bottleneck that came
   with trees and details was the GPU fetching vertices/indices of the imported pools from RAM over PCIe: 16 MB mirrors in
   VRAM, invalidated by `MEM_WRITE_WATCH`, cut the GPU work from ~1300 to ~700 ms every 2 s. Four runs
   (including Poco Path) without a crash and locked at 30 fps; the game had ~45 fps without a limiter, but stays capped at 30 by
   [USER]'s decision. `PVR_VRAM_MIRROR=0`/`PVR_NO_WRITE_WATCH=1` go back to the old path.
2. 🟢 **Smoothness / consistency (6.8):** at 30 fps, per-frame work is ~17–19 ms; spikes seen in tests
   are compilation/loading and pipeline captures. Only resume this investigation if the stutters become annoying again.
3. 🟢 **Visuals:** sky, terrain, trees/bushes, lighting, and fog over the valley were compared with Eden on the same save
   and time of day (`PVR_CLOCK_START`). The main image matches; only comparing/refining the distance blur remains, if
   [USER] points out a scene where it bothers.
4. 🟢 **Systems (phase 5):** audio and the name keyboard work and were confirmed by [USER]; save and clock persist.
5. 🟡 **APP / M7:** LAS-style overlay menu ready (F1/Esc; controller: Home or Back+Start): Controls, Video (monitor,
   fullscreen, VSync, FPS, scale, FSR1, SMAA), Audio, and Quit. Settings in `psvrecomp.ini`; if it dies during
   startup or within 300 frames after a change, the next start archives the ini as `.crashed` and uses defaults.
   **Next card:** start screen/launcher with Play, Settings, and Quit; it must hold the game's initialization until Play.
6. ⏸️ **60 fps:** `PVR_GAME60=1` exists as an experiment, but it is not in the menu and is not a target now.
7. ⏸️ **Rare crashes:** locker room and first battle stay logged below; only resume after the APP or if
   they become deterministic.

## Known issues (to hunt later)

- **Crash in the locker room (school, before "Head to the lighthouse")**, manual play by [USER] on 10/16, 1 occurrence,
  no steps to reproduce: `exception c0000005 accessing 0xffffffffffffffff` in `f_7000bf3dcc <- f_7000bf399c
  <- f_70027beaec <- f_7002b79458`. `f_7000bf3dcc` is the removal of an `unordered_map` node (libc++ `__hash_table`):
  the node read from the bucket (x19 = `32d102231b656757`) is garbage, i.e., the table was already corrupted (use after
  free / race between threads), not a translation error at that point. Log: `lab/host-vk/crash_vestiario_20261016.log`
  (has the session's `[input]`); save right after: `lab/saves/user_apos_vestiario_20261016`. If it repeats in the same
  place, it becomes a deterministic bug and is hunted through the caller.
- **Rare crash while loading the 1st battle** (~1 in 9 runs of the `user_antes_batalha_20261015` save, without
  limiter): `exception c0000005` in game functions, e.g. `f_7000c1e658 <- f_7000c1e5f8 <- f_7000e02cac` (lookup
  of a component with hash `0x3d3f8b275e8b9993` that returns null and the caller does not check) and another accessing `0x1e8`; once
  preceded by `OODLE ERROR: LZ corruption`. Hypothesis: a loading race that our timing exposes (on the Switch
  the object would already be ready). Logs: `lab/host-vk/stb3_3.run1.log`, `xs3.run1.log`, `stab_7.run1.log`,
  `stab_8.run1.log`. Deferred by [USER]'s decision (10/15).

- ~~Crash before Poco Path (`no function at 7002a1fc24`)~~ — fixed on 10/16. First logged as
  "corrupted vtable" (WRONG: it was deterministic, always at the same address). Real cause in gen.py: an 11-case
  switch in `f_7002a1f54c` had its function split where a neighboring function jumps into its middle (shared tail);
  the cases after the cut were rejected and fell into the global dispatch. See pipeline-log 10/16.

- ~~Invisible character in the open world~~ — fixed on 10/15 (occlusion query reported 0 pixels; see pipeline-log).

## Milestones

| Milestone | Objective criterion | Historical status (10/16; see audit for limits) |
|---|---|---|
| M0 Dump ready | `dumps/base/exefs/main` and `dumps/update/exefs/main` exist; build ids noted; romfs listed | ✅ gate dumps (run_id=131ff828b2) |
| M1 "Compiles" | Historical generated DLL/runtime path; exhaustive instruction coverage is tracked separately in phase 1 | 🟡 Later v4.0.0 boot evidence run_id=7adc0390c2; old run_id=990a33212b only reached init_sdk with an exception and cannot verify the old function count |
| M2 "Breathes" | log shows the game creating threads, opening services, and entering the frame loop (headless) | ✅ v400 run_id=7adc0390c2, base run_id=db35401e31 |
| M3 "First pixel" | automatic screenshot shows the Game Freak / The Pokémon Company logo | ✅ gate window (run_id=312d34de1a): screens rendered in the new game |
| M4 "Title" | title screen with music, and the controller navigates the menu | ✅ gate window (run_id=312d34de1a) + audio fixed 10/16 ([USER] confirms the sound) |
| M5 "New game" | creates a character, opening cutscene, controls the character | ✅ gate window (run_id=312d34de1a): the scene advances with input; name through the text box (10/16) |
| M6 "Open world" | walks around Paldea for 10 min without a crash; FPS measured | ✅ gate window --save (run_id=c6a80b10d8): 10 min in the open world without a crash at ~29 fps, simple automatic input (not free exploration) + test by [USER] (>10 min) |
| M7 "App" | own launcher, settings, extra features | 🟡 name PSV Recomp, psvrecomp.ini, crash report |

## Differences from Zelda (main risks)

| Topic | Zelda LA (2019) | Pokémon Violet (2022) | Impact |
|---|---|---|---|
| Code size | medium | ❓ probably **several times larger** (open world, bigger engine) | generation and compile time; 32 GB of RAM may be tight when compiling |
| Symbols | SDK with `nn::` symbols | ❓ check in phase 0 (`.dynsym`, `.eh_frame`) | no symbols = more manual RE |
| Modules | `main` + `sdk` | ❓ may have `subsdk*` (middleware) | the generator needs N modules |
| Graphics | NVN, small scenes | NVN, open world, many shaders, ❓ compute/tessellation | more work in the shader translator and the backend |
| Data formats | BFRES/BNTX/SARC (Nintendo) | ❓ Game Freak's own formats (`trpfs`, FlatBuffers `tr*`) | the **game** reads the data; we only need a parser for study/mods |
| Threads | few | ❓ many (world streaming) | synchronization (arbitration SVCs) must be solid |
| Online | none | Union Circle, Tera Raid, Poké Portal | **stub**: network services answer "offline" |
| Performance on Switch | good | poor (FPS drops) | native on PC should do better, but depends on the Vulkan backend |

## Strategy (decisions made)
1. **Start from a local fork of LAS Recomp (MIT)** for the generator and the runtime: lifter, SIMD in C, jump tables
   via Unicorn, kernel, IPC, NVN→Vulkan. Rewrite only what is Zelda-specific (game `hle/`, `patches.py`,
   randomizer, UI). Keep the MIT copyright notice.
2. **Eden (GPL-3) is a reading reference**: semantics of SVCs, services, and the Maxwell shader recompiler.
   Understand and reimplement; do not paste code.
3. **REA/Ghidra** to understand the game's code (phase 7/9). LAS did RE by instrumenting the recompiled game; we
   have both.
4. **Always an oracle**: Unicorn for instructions; Eden running the same dump as the **behavior reference**
   (what the game should see/do) when the recompiled build diverges.
5. **Division of labor**: Claude designs and verifies; local models execute cards. Each phase lists what is a worker card.

## How to follow along
- Each phase has its own page with `[ ]` → `[x]` tasks, who executes them (🤖 local model / 🧠 Claude), and the exit criterion.
- Every card goes into `docs/pipeline-log.md`. Findings go into `docs/`, and nothing from the game is copied there.
