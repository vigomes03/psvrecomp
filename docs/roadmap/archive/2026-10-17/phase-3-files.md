# Phase 3: File system and game data

**Audit (2026-10-17):** partial, not all of 3.1-3.4.
`runtime/services/fs.c:375-388` opens a raw `<g_romfs_dir>.bin` storage image. Extracted inputs and runtime storage
must not be conflated. v4.0.0 inputs are under `dumps/v400/` (run_id=131ff828b2).
Reading during gameplay has historical evidence (run_id=c6a80b10d8); that does not prove runtime base/update layering
or asynchronous-read latency. Save/load was manually reported by [USER] in the pipeline log.
**3.4 remains partial:** `fs.c:568` treats Commit as a no-op, so atomic commit is not established.
**3.5 remains open:** no package parser was located in the inspected project tree; coordinate with 9.3/10.2.

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

## Historical status on 10/15 (superseded by the audit above)
- 🟢 In practice, the phase is covered by the LAS port: the game reads romfs/trpfs alone and the **save is persistent**
  (close, reopen and load works — manual test by [USER]). This does not close all requirements in 3.1-3.4; 3.5
  (study parser) remains open.

## Exit criteria
Log of `fsp-srv`: every file requested at boot is found; no unexpected `PathNotFound`; save creates and reads.

## Risks
- Hash of name instead of path inside the `trpfs`: irrelevant for running (the game resolves it), relevant for studying.
