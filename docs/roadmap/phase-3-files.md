# Phase 3: File system and game data

**Objective:** the game reads its own files (base romfs + update) through the `fsp-srv` service, exactly as on the console.
**The game** interprets the formats; we just serve bytes. Custom parsers are for study/mods (phase 9).

**In Zelda:** `services/fs.c` serves the extracted romfs; `romfs_build.c` builds a romfs with files swapped by the
seed (layering). Saves in its own folder.

## Tasks
- [ ] 3.1 🧠 Decide: serve the **extracted romfs** (folder, simple, like LAS) or read the **NCA directly** (without
  extracting 7+ GB). Start with the folder.
- [ ] 3.2 🤖 Base + update layering: update file overrides the base file (`dumps/update/romfs` over `base`).
- [ ] 3.3 🤖 `fsp-srv`: `OpenFileSystemWithPatch`/`OpenDataStorageByCurrentProcess`, `IStorage::Read` large,
  **asynchronous/parallel** reads (open world streaming): measure latency.
- [ ] 3.4 🤖 Save data: `OpenSaveDataFileSystem` → `save/` local, with atomic commit.
- [ ] 3.5 🤖 (Study, parallel) Parser of `trpfd`/`trpfs` in Python to **list** the content (names/hashes),
  with the criterion "list matches what the game requests in the `fsp-srv` log".

## Status on 10/15 (review with [USER])
- 🟢 In practice, the phase is covered by the LAS port: the game reads romfs/trpfs alone and the **save is persistent**
  (close, reopen and load works — manual test by [USER]). 3.1-3.4 remain as "handled by the port"; 3.5
  (study parser) remains open.

## Exit criteria
Log of `fsp-srv`: every file requested at boot is found; no unexpected `PathNotFound`; save creates and reads.

## Risks
- Hash of name instead of path inside the `trpfs`: irrelevant for running (the game resolves it), relevant for studying.
