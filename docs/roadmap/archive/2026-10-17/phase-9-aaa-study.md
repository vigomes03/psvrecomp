# Phase 9: Understanding the Game (AAA Study) (continued)

**Audit (2026-10-17):** research deliverables remain open. Runtime fixes and diagnostic hooks are useful
inputs, not substitutes for the reviewed architecture/format notes in `docs/re/` (directory not found in this audit).
Priority proposal for the platform experiment: 9.3 package/index and scene references, then 9.2 scene-loading trace,
with narrowly scoped 9.1 entity/loader and 9.6 collision middleware work only as needed.
Defer battle AI/damage/Terastal, exhaustive engine/middleware coverage and the Zelda comparison unless needed.
These are proposals, not new user-approved deferrals. No new RE experiment was run in this audit.

**Objective of IDEA.md:** understand how an AAA game is made. Recompilation is the means; this phase is the end.
All documented in `docs/re/` as **description** (architecture, flows, names, short offsets), without copying
decompiled code or assets.

## Study Tracks
- [ ] 9.1 **Engine Architecture**: main loop, threads (who does what), task scheduler, memory allocators
  (heaps), entity/component system.
- [ ] 9.2 **Open World Streaming**: how Paldea is divided, loaded and unloaded; LOD; what causes FPS drops on Switch.
- [ ] 9.3 **Data Formats**: `trpfs`/`trpfd` (packages), models/materials/skeletons/animations (FlatBuffers
`tr*`), textures, scripts/events, data tables (Pokémon, moves, items, encounters).
- [ ] 9.4 **Rendering**: frame passes (via `PVR_DEBUG_FRAME`), main shaders, shadows, sky/weather.
- [ ] 9.5 **Game Systems**: battle (damage calculation, AI), Terastal, spawn/encounters in overworld, Pokémon
followers, day/night cycle and weather.
- [ ] 9.6 **Middleware**: what is from Game Freak and what is third-party (physics, audio, network, UI).
- [ ] 9.7 **Comparison** with Zelda LA: what is the same (SDK, NVN) and what changes in an open-world AAA engine.

## How We Work Here
- Question → `rea_worker` card (🤖) → review (🧠) → note in `docs/re/<tema>.md` with marking
  ✅ verified / 📖 read / ❓ hypothesis and evidence (evidence_id, address+build id).
- Format parsers in `psvrecomp/tools/formats/` (🤖 cards, criterion: reads 100% of files of that type
  without error + test with file from `lab/`).
