# Phase 6: Playable

**Audit (2026-10-17):** new-game scripted scene progression has gate run_id=312d34de1a;
600 seconds from a copied open-world save has gate run_id=c6a80b10d8 (17,227 frames, final windows 28.9 fps).
This is not random exploration or whole-game stability. 6.1/6.2 are partial (input/collection exist; semantic
checkpoints and automatic triage need coverage). 6.3 is ongoing. 6.4/6.6 have measured improvements, not a
per-area/thread coverage matrix. 6.5's random component remains open. 6.8 has warm-cache measurements;
cold-cache and monitor pacing remain open. 6.9 is **deferred by [USER]**, not missing mandatory work.
The deterministic `7000cedb00` failure in 6.7 is recorded as addressed in the pipeline log (2026-10-15);
rare first-battle loading and locker-room crashes remain deferred, not resolved.

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

- [ ] 6.6 **Partial / regression coverage:** retain a repeatable 30 fps route matrix after the recorded CPU/GPU improvements (pipeline log, 10/15-10/16). Historical open-world sample: run_id=c6a80b10d8. The old 3 fps baseline and flush diagnosis are not current status.
- [ ] 6.7 🟢 1st battle crash (see phase 1, item 1.7): fixed, proven by run_auto (4365 frames) and by [USER]; no gate.
- [ ] 6.8 🧠 **Smoothness:** per-frame measurement (1% low, cause of spikes) → precompiled shaders → tracking of texture
  writes → less CPU↔GPU sync → presentation pacing by the monitor. Tests always at 30 fps.
- [ ] 6.9 **Deferred by [USER]:** 60 fps (`PVR_GAME60`); menu/ini option, per-version address, long sync test.

## Historical status on 10/15 (superseded by M6 evidence in the audit above)
- 🟢 **M5 reached and M6 partial** in the manual test: intro and start of the story, more than 10 min without a crash, save ok.
  Small visual bugs (score 95/100): skybox with lines, lighting, objects not rendered. [USER] points out the places and
  creates saves for the search.

## Exit criterion (M5 → M6)
M5: new game until controlling the character. M6: 10 min in the open world without a crash, FPS logged in `docs/`.
