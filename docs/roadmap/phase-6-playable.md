# Phase 6: Playable

**Goal:** from a new game to exploring Paldea with measured stability and performance.

**In Zelda:** `shot.sh <frame>` loop with scripted input (`LARECOMP_INPUT`), direct warp to stages, save in a temporary
folder, compared screenshots; fixes bug by bug, with a comment explaining why.

## Tasks
- [ ] 6.1 🧠 Test scripts (`PVR_INPUT`): title → new game → first cutscene → character control.
- [ ] 6.2 🤖 Run the scripts in a batch, collect screenshots/logs, automatic **triage** (crash? black screen? FPS?).
  Output: `work/notes/triagem-<date>.md` for Claude to prioritize.
- [ ] 6.3 🧠 Each bug: root cause (`systematic-debugging` skill) → fix card 🤖 or fix 🧠 if it is in the core.
- [ ] 6.4 🤖 Performance: `fnprof` (hot functions), FPS per area, CPU use per thread. The original game runs at
  ~30 FPS with drops; initial target: stable 30 FPS, then unlock (phase 8).
- [ ] 6.5 🧠 Stability: 10 min of exploration without a crash (script + random).

- [ ] 6.6 🟢 **Performance (urgent) — 30 fps reached 10/15 (run_auto, no gate):** 5-10 fps indoors, ≈3 fps in open areas, CPU ~9 %, GPU idle. The log shows
  ~60 thousand CPU↔GPU flushes per run (each command list sent and waited on one by one). Target: 30 fps indoors.
- [ ] 6.7 🟢 1st battle crash (see phase 1, item 1.7): fixed, proven by run_auto (4365 frames) and by [USER]; no gate.
- [ ] 6.8 🧠 **Smoothness:** per-frame measurement (1% low, cause of spikes) → precompiled shaders → tracking of texture
  writes → less CPU↔GPU sync → presentation pacing by the monitor. Tests always at 30 fps.
- [ ] 6.9 60 fps (`PVR_GAME60`): menu/ini option, per-version address, long sync test.

## Status on 10/15 (review with [USER])
- 🟢 **M5 reached and M6 partial** in the manual test: intro and start of the story, more than 10 min without a crash, save ok.
  Small visual bugs (score 95/100): skybox with lines, lighting, objects not rendered. [USER] points out the places and
  creates saves for the search.

## Exit criterion (M5 → M6)
M5: new game until controlling the character. M6: 10 min in the open world without a crash, FPS logged in `docs/`.
