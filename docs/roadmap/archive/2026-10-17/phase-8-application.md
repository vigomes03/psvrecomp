# Phase 8: The application

**Audit (2026-10-17):** M7 remains partial.
8.2 has code and recorded run_auto/manual observations (pipeline log, 2026-10-16), but no dedicated menu gate;
physical controller navigation and the full settings matrix remain unverified. Its checkbox stays open.
8.1 launcher is pending; 8.3 is deferred by [USER]; 8.4 and 8.6-8.8 are future proposals, not core-runtime blockers.
8.5 remains partial: exposed options do not establish visual/performance correctness.

**Goal:** turn "the game running" into an application of our own, like LAS Recomp is for Zelda.

**In Zelda:** start screen (ImGui) with file setup and code build **on the player's machine**; F1 overlay
menu; unlocked aspect ratio (FOV/aspect/culling patches); internal resolution, SMAA, FSR1; remappable
controls; save editor; tracker; randomizer.

## Tasks
- [ ] 8.1 🤖 Launcher: pick the dump folder (base + update), validate build ids, generate/compile the code (with
  a progress bar, like LAS's `gamebuild.c`), settings.
- [ ] 8.2 **Partial; menu code/observations exist, full acceptance pending.** 🤖 Overlay menu (F1 / Esc; controller: Home or Back+Start), in English like LAS: tabs Controls (layout),
  Video (fullscreen, monitor, VSync, FPS, internal resolution, upscaler, SMAA), Audio (volume), Quit. `runtime/ui/menu.cpp`
  (from `menu.mm`), LAS's `option_rows.cpp`/`osk.cpp`, Dear ImGui in `third_party/imgui`. Test: `PVR_MENU_KEYS=<frame>:<key>,...`
  + `LARECOMP_WINDOW_SHOT`. Target FPS stays at 30 ([USER]'s decision 10/16). **Safe start:** if the process dies during
  startup or within 300 frames after changing options, the next start archives `psvrecomp.ini` as `.crashed` and uses defaults.
- [ ] 8.3 🧠 **FPS unlock** (30 → 60+): the `PVR_GAME60=1` experiment exists, but is on hold by [USER]'s decision;
  do not put it in the menu before he asks for it and before physics/animation/cutscenes are tested.
- [ ] 8.4 🧠 **Widescreen/ultrawide**: camera aspect + culling + anchored UI (LAS's `patches.py` technique).
- [ ] 8.5 🧠 Internal resolution, FSR1 upscaler, and LAS's SMAA anti-aliasing: already exposed in the Video tab; a
  visual/performance test matrix per combination is still missing to validate the feature.
- [ ] 8.6 🤖 Draw distance / LOD (the Switch cuts a lot in the open world).
- [ ] 8.7 🤖 Study tools inside the app: free camera, on-screen Pokémon stats viewer, warp.
- [ ] 8.8 💡 Future ideas (after M7): save editor, our own randomizer, data mods read from `trpfs`.

## Rule
Everything **local**. No packaging for distribution (`make dist` is not a goal).
