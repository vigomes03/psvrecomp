# Phase 0: Acquisition and Recognition

**Objective:** have the game's code and data extracted (base + update) and know **what we're dealing with**
before writing a line of the recompiler. This phase decides the scale of everything else.

**In Zelda:** the user provides `extracted/exefs` and `romfs`; `tools/nso.py` reads the NSO and `tools/analyze.py`
performs the function and instruction census.

## Tasks

### 0.1 Keys and Extraction 🧠 (with [USER])
- [ ] `prod.keys`/`title.keys` from the [USER]'s console (Lockpick_RCM) to `keys/` (ignored)
- [ ] `hactool` on XCI → `secure` partition → identify the Program NCA (base 1.0.0)
- [ ] Extract `exefs` (main, sdk, subsdk*, rtld, main.npdm) → `dumps/base/exefs/`
- [ ] Extract `romfs` → `dumps/base/romfs/`
- [ ] Dump the **update** (NSP from [USER]): apply the patch (BKTR) with hactool `--basenca` → `dumps/update/`
- [ ] Note: game version, Title ID, **build id** of each NSO, SDK version (string `NintendoSdk_*` in the NSO footer)

**Decision:** recompile **only one version** (probably the last of the update), because addresses, patches, and hooks are per build id.

### 0.2 Executable Inventory 🤖 (script cards) + 🧠 review
- [ ] Run `nso.py` from LAS on each NSO: size of `.text/.rodata/.data/.bss`, `MOD0`, imports/exports
- [ ] Count functions: `.eh_frame_hdr` × symbols × BL targets (`analyze.py`)
- [ ] **Symbols:** how many `STT_FUNC` with names? (does `main` have names or just the SDK?)
- [ ] Instruction census: % FP/SIMD, rare instructions (LSE atomics? ARMv8.1+? does LAS lifter cover ARMv8.0 + crypto + CRC32)
- [ ] List **middleware** by strings (Havok? Wwise/CRI? Pia (network)? FlatBuffers?) and by `subsdk*`
- [ ] List of **IPC services** used (strings `"fsp-srv"`, `"nifm:u"`...), phase 2 work list
- [ ] List of imported **NVN** functions (`nvn*` via `nvnBootstrapLoader`), phase 4 work list
- [ ] Romfs inventory: extensions, sizes, `*.trpfs`/`*.trpfd` (Game Freak package files)

### 0.3 First Look in Ghidra/REA 🤖 (rea_worker) + 🧠
- [ ] Load `main` (ELF converted from NSO, or Ghidra's NSO loader) and check that REA can analyze
  a binary of this size (time, RAM). If it doesn't work in CLI (20 s per call × reimport), use MCP session.
- [ ] Find `nnMain`, the main loop and the threads created during initialization

### 0.4 Behavior Reference 🧠
- [ ] Compile/run **Eden** with the same dump (keys needed): confirms that the dump is intact and provides an
  oracle of "how it should be" (SVC/IPC logs from Eden vs ours)

## Output / criterion (M0)
`docs/roadmap/phase-0-findings.md` with: versions, build ids, sizes, number of functions, symbol coverage, % SIMD,
middleware, services, NVN functions, romfs formats. With this we review phases 1 to 4 (time and order).

## Risks
- Giant `.text` → generation (Python) and compilation time: measure here (generate only 1% and time).
- Instructions outside of ARMv8.0 → the lifter needs to grow.
