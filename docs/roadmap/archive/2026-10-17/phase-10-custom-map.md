# Phase 10: Custom map with a platform (exploratory)

**Audit (2026-10-17):** planning only; every implementation checkbox remains open.
First target is replacement of a small area, not a standalone map independent of original resources.
All strategies require experiments: `fsp-srv` exposes the outer romfs package, not necessarily inner resource hashes.
A RomFS override does not automatically replace a resource inside `data.trpfs`; interception may need the archive
reader or package/index rebuilding. Collision format and scene registration are unknown.
No evidence links the recorded hash-table crash to map ids. Integrity checks may also exist inside the package;
filesystem interception does not by itself bypass them. Proposed hook names below are not existing APIs.

**Goal:** make the game load an area of our own (at minimum a flat platform with collision and a spawn point),
without depending on an original map. This is personal, local study on our own dump (same rules as phase 9:
nothing from the game goes into git, and the notes are **descriptions**, without copying assets or decompiled code).

**Status:** ⬜ not started. Depends on 9.2 (streaming) and 9.3 (formats). Today we **do not know** how the game
defines, loads, and registers a map. Everything below marked ❓ is a hypothesis until there is evidence.

## Prerequisites
- Phase 3 🟢: the game reads the romfs (base + patch) and the `trpfs`.
- Phase 7 🟢: `fnprof`, `PVR_*` hooks, `run_auto.sh`, gates, REA/Ghidra.
- Phase 9.3: parser for `trpfs`/`trpfd` and the `tr*` FlatBuffers (read-only at least).

## Strategies (from most to least feasible)
| # | Strategy | Idea | Risk |
|---|---|---|---|
| A | **File override** | The recomp already controls `fsp-srv`: when the game asks for file X (by path hash), we serve our file Y | medium: needs a file generated in the exact format |
| B | **Edit a small area** | Replace the contents of a simple interior with a platform (mesh + collision + spawn) | medium: few dependencies |
| C | **New scene + warp by code** | A `PVR_*` hook that forces the scene loader to open an id of ours | high: requires understanding the scene manager |
| D | **Open world (streaming cell)** | Replace one cell of the Paldea grid | very high: LOD, spawns, occlusion, neighbors |

Plan: **B via A** first (the smallest possible map), then C, and only then D if it makes sense.

## Steps

### 10.1 Observe how the game loads maps (read-only)
- [ ] 10.1.1 🤖 Log of `fsp-srv` reads (path/hash, offset, size, thread, timestamp) enabled by
  `PVR_FSLOG=1` (name ❓; follow the pattern of the other hooks).
- [ ] 10.1.2 🤖 Automatic script: (a) standing at the same spot for 30 s, (b) a straight walk in the open world,
  (c) entering and leaving a house, (d) fast travel. Each script produces a separate log, with a `run_id`.
- [ ] 10.1.3 🤖 Script that groups the logs: files read only on scene changes, files read continuously
  (streaming), and repeated files (cache). Output in `work/`, **outside git**.
- [ ] 10.1.4 🧠 Review: which files make up "a small map" (interior)? Note in `docs/re/maps.md` with
  ✅/📖/❓ and evidence.

### 10.2 Decode the formats involved
- [ ] 10.2.1 🤖 `trpfs`/`trpfd` parser: lists files by hash and extracts them to `work/` (criterion: reads 100% of the
  packages without errors).
- [ ] 10.2.2 🤖 For the files found in 10.1.4, work out the FlatBuffers schema (fields, types, references
  between files). Sources: strings/vtables in the binary, REA/Ghidra on the code that reads the file, comparison of two
  different maps.
- [ ] 10.2.3 🤖 Identify, by type, the role of each file: mesh/model, material, texture, collision,
  objects/props, spawn point, script/event, lighting/sky, navigation.
- [ ] 10.2.4 🧠 Round trip: read a file, rewrite it **without changes**, and compare byte by byte (or semantically).
  Only move on with this green.

### 10.3 Prove the file override (without changing content)
- [ ] 10.3.1 🤖 Mechanism in `fs.c`: a `mods/` folder (gitignored) mapping hash → replacement file, logging
  each replacement. Off by default (`psvrecomp.ini`).
- [ ] 10.3.2 🤖 Test: replace a file with an **identical copy** and confirm the game behaves the same
  (gate `window`, same reference `run_id`).
- [ ] 10.3.3 🤖 Test: change **one trivial field** (e.g.: the position of a prop or a material color) and see the change on
  screen. This proves the format was understood and that the game accepts modified data.

### 10.4 Minimal platform in an interior
- [ ] 10.4.1 🤖 Mesh: a flattened cube/plane in the game's model format, with the material and texture of an object
  that already exists (reusing the material avoids touching shaders).
- [ ] 10.4.2 🤖 Collision: the same shape in the collision format. Test: the character walks on the platform and does not
  fall through the floor.
- [ ] 10.4.3 🤖 Spawn: a valid entry point inside the platform, so the player appears on it and does not fall.
- [ ] 10.4.4 🤖 Cleanup: remove the interior's original props or keep them (decide by whichever is more stable).
- [ ] 10.4.5 🧠 Manual gate: enter the house and see the platform, walk on it, leave. Record the `run_id` and screenshot
  in `work/`, not in git.

### 10.5 Own scene called by code (optional)
- [ ] 10.5.1 🧠 Map the scene loader: who receives the scene id, who decides the transition (fade), which
  data tables register a scene (e.g.: warp/zone table ❓).
- [ ] 10.5.2 🤖 `PVR_WARP=<id>` hook that triggers the transition to our id (from the F1 menu or a
  shortcut).
- [ ] 10.5.3 🤖 Register a new entry in the data tables (via override) pointing to our files.

### 10.6 Authoring tools (if 10.4 works)
- [ ] 10.6.1 🤖 Python generator (`psvrecomp/tools/formats/`): simple description (JSON: platforms, position,
  size, material) → files in the game's format.
- [ ] 10.6.2 🤖 Validator: rereads what was generated with the 10.2 parser and checks references and limits.
- [ ] 10.6.3 🧠 Optional: bridge to Blender/Unity to draw the mesh and export it to the generator.

### 10.7 Open world (only if everything above is solid)
- [ ] 10.7.1 🧠 Understand the streaming grid (9.2): cell size, neighbors, LOD, link to spawns.
- [ ] 10.7.2 🤖 Replace **one** distant, isolated cell with flat terrain and test unload/load when going and
  coming back.

## Known risks
- **Hashes and cross-indexes:** many formats reference others by hash. A wrong id can become a crash
  (like the `unordered_map` corruption already seen, see the roadmap README). Always test with `run_auto.sh` and a gate.
- **Shaders/materials:** a new material may need precompiled shader variants. That is why we reuse
  existing materials.
- **Occlusion and navigation:** the game may require extra data (occlusion, navmesh, baked lighting). If missing, it will be
  dark or disappear; the first test should only be "something shows up".
- **Integrity checks:** if there is a package hash, overriding at the `fsp-srv` level avoids the problem,
  because we do not change the original package.
- **Version dependency:** ids and hashes may change between the base and v4.0.0. The target is **v4.0.0**.

## Done criteria (milestones)
| Milestone | Proof |
|---|---|
| M10a | read log of an interior vs the open world, with the map files identified (10.1) |
| M10b | identical override = same behavior; override with one changed field = visible change (10.3) |
| M10c | custom platform in an interior, with collision and spawn, walkable (10.4) |
| M10d | own scene called by `PVR_WARP` (10.5) |

## How we work
Same flow as phase 9: question → `rea_worker` card (🤖) → review (🧠) → note in `docs/re/` with
✅ verified / 📖 read / ❓ hypothesis and evidence (evidence_id, address + build id). Extracted data, mods, and logs
stay in `work/`/`mods/` (gitignored); only our tools' code and the notes go into git.
