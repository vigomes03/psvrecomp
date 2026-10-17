# LAS Recomp study: how it was made

> Analysis done **by reading the code** (without REA), on 10/14/2026, on the `LASRecomp-main` zip
> (= `github.com/peiikai/LASRecomp`, 2 commits before HEAD). Everything marked ✅ was
> executed on this machine; the rest comes from reading the code and the comments.

---

## 1. What it is, in one sentence

A **static recompilation** of *Zelda: Link's Awakening* (Switch, 2019): the game's **ARM64** machine code
is translated **once, offline**, to **C**, and that C is compiled to x86-64 (or ARM64) and linked
with a **runtime** that imitates the Switch operating system (Horizon) and the graphics API (NVN → Vulkan/Metal).
**It is not an emulator:** there is no interpreter or JIT. The game's functions become native C functions.

Size: about **51 thousand lines of its own** (runtime in C/ObjC/C++ and tools in Python), plus the third-party
randomizer (LAS-Randomizer) with about 8 thousand lines of adaptation.

| Area | Lines | What |
|---|---:|---|
| `tools/` recompiler (`nso`, `analyze`, `lifter`, `simd_c`, `gen`, `patches`) | ~3,250 | ARM64 → C |
| `runtime/nvn/` | ~14,500 | NVN graphics API + Maxwell shader translator + Vulkan/Metal |
| `runtime/ui/` | ~6,400 | start screen, overlay menu (ImGui), tracker, save editor |
| `runtime/hle/` | ~6,000 | replacements for game/SDK functions and new features |
| `runtime/services/` + `kernel.c` + `ipc.c` + `loader.c` | ~3,800 | fake "Horizon OS" |
| `tools/rando/` | ~8,000 | randomizer (entrances, rooms, pots/bushes/digs, shops...) |

---

## 2. Architecture

```
 OFFLINE (on the player's PC, on first run)                       AT RUNTIME
 ────────────────────────────────────────────────                ─────────────────────────────────────────
 extracted/exefs/main, sdk (NSO, ARM64)                           lasrecomp.exe  (runtime, no game code)
        │ tools/nso.py   (LZ4, segments, MOD0, dynsym, relocs)         │ loads lasgame.dll (game code)
        ▼                                                              ▼
 tools/gen.py  ──►  discovers functions  ──►  tools/lifter.py     loader.c  → maps NSO at 0x70_0000_0000,
   (eh_frame, symbols, relocs, BL targets, ADR/ADRP+ADD,          applies relocs, binds imports to HLE stubs
    fixed point splitting functions)           │ 1 instruction → C  kernel.c  → SVCs (threads, mutex, events, memory)
   jump tables resolved by EMULATING           │ FP/SIMD: asm (ARM)  ipc.c + services/ → sm:, fsp-srv, hid, audren, time...
   the snippet with Unicorn                    │   or portable C    hle/      → SDK/game functions replaced by C
        ▼                                     (simd_c.py)          nvn/      → NVN → Vulkan (Win/Linux) | Metal (mac)
 generated/main/*.c, sdk/*.c  (~1,500 functions/file)                          Maxwell shaders → GLSL/MSL → SPIR-V
        │ clang -O1 (dev)  |  zig cc (player)                      ui/       → ImGui: start screen, F1 menu, tracker
        ▼                                                         rando     → seed picks instructions/files
 lasgame.dll  (+ lasgame.dll.id = hash of generator+flags)
```

### Boot flow (`runtime/main.c`)
`plat_init` → start screen (`launcher_run`) → `boot()`: `gamelib_load` (game DLL) → `loader_load(exefs)`
→ `rando_boot` (seed patches) → `kernel_init` → `dispatch_init` → reads `main.npdm` (priority/stack) →
calls the game's `nn::init::Start` on a "guest" thread. `ui_run()` keeps the window and input on the main
thread; changing seed or returning to the title does an **in-place reboot** (`RT_ON_RESET` clears the state).

---

## 3. The recompiler (`tools/`) step by step

1. **`nso.py`**: reads the NSO (the Switch executable format): decompresses LZ4, builds the image
   (`.text/.rodata/.data/.bss`), reads `MOD0`, the dynamic table, the symbols (`dynsym`), and the relocations.
2. **Function discovery** (`gen.py: boundaries` + `main`):
   - `.eh_frame_hdr` (the C++ unwind table = start of almost every function);
   - `STT_FUNC` symbols, `R_AARCH64_RELATIVE` targets (vtables and pointers);
   - every `BL` target, addresses materialized with `ADR` / `ADRP+ADD` (callbacks);
   - **fixed point**: any branch out of its own function becomes a new start and splits the function,
     until nothing new appears.
3. **Lifter** (`lifter.py`): decodes **each 32-bit word by hand** (no Capstone on the critical
   path), instruction by instruction, and generates C over `struct Cpu` (`x[31]`, `sp`, `nzcv`, `v[32]`...).
   Flags are computed only in the instructions that set them (`adds64`, `subs64`...). LDXR/STXR become
   compare-and-swap. An unsupported instruction becomes `rt_udf()` (loud failure, not silent).
4. **FP/SIMD**: two strategies.
   - On an ARM64 host (Mac M1+), the instructions are **re-emitted as inline asm**, in batches of up to 24,
     loading/saving the V registers of `Cpu`. Bit-exact by construction.
   - On x86 (Windows/Linux), `simd_c.py` + `runtime/simd.h`: each encoding becomes a call to a `static inline`
     helper with constants, and clang folds the `switch`es. Requires AVX2/FMA (`-march=x86-64-v3`).
5. **Jump tables** (`br xN`): instead of heuristics, they **emulate with Unicorn** the snippet between the `cmp` and the `br`
   for every possible index and collect the targets. What they cannot resolve falls back to "every
   instruction of the function is a label" + `switch(pc)`. That way a forgotten case still lands correctly.
6. **Emission** (`emit_function`): each function becomes `void f_<addr>(Cpu *c)`. Internal branch = `goto L_x`;
   direct call = C call; tail call/indirect = `__attribute__((musttail)) return rt_dispatch(c)`.
   `musttail` keeps the host stack from growing in chains of jumps.
7. **Output**: chunks of about 1,500 functions or 1.5 MB of C (a giant function gets its own file, to
   compile in parallel) + `main_table.c` (address → pointer). `write_if_changed` makes `make` only
   recompile what changed.

### Runtime dispatch (`dispatch.c`)
A 4096-entry direct-mapped cache per thread in front of a binary search over the tables.
Fake addresses `HLE_BASE + 16*i` point to host C functions. `hle_override` replaces any
game function by address.

---

## 4. Design decisions (and why)

| Decision | Why / effect |
|---|---|
| **Guest address = host address** (fixed window `0x70_0000_0000..0x73_2000_0000`) | Load/store becomes `*(uint32_t*)addr`, with no translation. On Windows, `VirtualAlloc` reserves and a *vectored exception handler* commits on demand. |
| **Recompile on the player's PC** (Python generator packaged with PyInstaller + `zig cc`) | The release **contains no Nintendo code**; everyone generates their own from their own dump. The legal question is solved by architecture. |
| `GAMELIB_ID` = hash of generator + headers + flags | An old DLL is never loaded with a new runtime: it is recompiled. |
| **HLE by symbol name** (`HLE_FUNC("_ZN2nn3hid12GetNpad...", fn)`) registered via **linker sections** | The SDK (`nn::`) ships with symbols. You just write the C function and it "shows up" on its own, with no central table, on the 3 OSes (Mach-O/ELF/PE with `.hle$a/m/z`). |
| The whole **NVN** API (495 functions) intercepted by name via `nvnBootstrapLoader` | They do not emulate the Maxwell GPU at register level; they reimplement the API on top of Vulkan/Metal. |
| Command buffers recorded **in the game's own memory** | The game's memory management and "out of memory" callbacks keep working as designed. |
| Shaders: **Maxwell binary (SASS) → MSL**, and GLSL by token rewriting of the MSL | A single translator; GLSL compiled with shaderc. Branches become a `switch(pc)` state machine with SSY/PBK stacks. |
| **`patches.py`**: per-instruction patch that **checks the original word** (`assert w == 0xbd457369`) | A wrong address or wrong game version fails at generation time instead of becoming a silent bug. Used for widescreen, FOV, culling, warp. |
| **Randomizer in code**: `patch_variants.json`, where the seed picks the instruction at runtime (`rando_word`) | One DLL serves all seeds; changing seed needs no recompilation or restart. |
| `RT_ON_RESET` (also via a linker section) | In-place reboot: each module declares what to reset. |
| `-O1` on generated code | Millions of lines of C; `-O2` would cost a lot of compile time for little gain. |
| Comments say **why** (address, what the game does, which seed/bug showed the problem) | The code is the reverse engineering documentation. E.g.: `doorjump.c` explains the `PlayerCollision` struct, the vtable, and the offset. |

---

## 5. How they did the reverse engineering (no Ghidra in the repository)

There is no Ghidra/IDA project in the repo. The RE was done by **instrumenting the recompiled game itself**:

- **SDK symbols** (mangled `nn::...`) + `tools/sym.py` (address → symbol + disassembly with Capstone + `c++filt`).
- **`LARECOMP_FNPROF=<from>:<to>`**: every generated function calls `FN_ENTER`. They count the entries between two
  frames and **compare two runs** to see which game functions an action triggers.
- **`LARECOMP_ADDF_MATCH`**: "pokes" every float/double in the game's memory near a value and sees what
  moves Link, to find the real position through a **memory bisection** (this is how `PlayerCollision+0x80` was found).
- **248 `LARECOMP_*` variables** as debug hooks: scripted input, warp to stage X, seed, save in a temporary
  folder, screenshot at frame N, Vulkan device-lost trace, per-frame draw log...
- `str` hooks via `patches.py` to **find out where an object lives** (e.g.: the "level jump request" object).

## 6. Workflow (how they developed it)

- **Made almost entirely by AI**: the README says the code, the tools, the RE, and the documentation were written by
  **Claude (Claude Code)**, "directed, tested, and reviewed by a human".
- The public history is **squashed**: 12 commits, the first being "LARecomp Beta 3". Planning lived in
  `notes/PLAN.md` (mentioned in a comment, **not published**).
- **Differential tests against an oracle** (the strongest point of the project):
  - `test_lift.py`: instruction by instruction, generated C vs Unicorn, with edge values;
  - `test_simd.py`: enumerates the **entire** FP/SIMD encoding space, compares validity and results with Unicorn
    (NaN, ±0, denormals, rounding modes);
  - `test_translate.sh`: shader translator fuzzing: MSL byte-identical to a reference translator, GLSL compiles
    (shaderc) and validates (SPIRV-Tools);
  - `test_vk_pipelines.sh`, `test_astc.sh`: real Vulkan pipelines, ASTC decoder vs reference.
- **Automated visual validation**: `shot.sh <frame>` runs the game with scripted input and saves a PNG;
  `montage.sh`, `frames.sh`, `transients.py` (flicker between frames), `bandmetric.py` (banding),
  `passes.py` (groups draws by shader/render target).
- **Gameplay tests**: `doorjump_test.sh <seed>` walks every incompatible door of the dungeon shuffle;
  they generate several seeds and check that every location is reachable.
- **Performance**: `perf_sweep.py`, `fnprof`, `sampletree.py` (tree from macOS `sample`).
- Rules (`CONTRIBUTING.md`): **no Nintendo files** in the repo; "a fix is only verified when you have seen it
  work"; changing Metal requires the matching Vulkan change; old seed IDs must keep loading.

---

## 7. Tools used (and what I installed here)

| Tool | Role | Here |
|---|---|---|
| **Python 3.12** + `capstone` 5.0.9, `unicorn` 2.1.4, `lz4` 4.4.5 | recompiler / differential tests | installed: `tools/venv` (uv, CPython 3.12.13) |
| LAS-Randomizer: `oead`, `evfl`, `keystone-engine`, `quicktex`, Pillow, PyYAML | generate seeds | ✅ `third_party/LAS-Randomizer/venv` |
| **MSYS2 UCRT64**: clang 23, lld, make, SDL3, FFmpeg, Vulkan headers/loader/validation, shaderc, SPIRV-Tools, VMA, gdb, nasm | build the runtime | ✅ **`D:\msys64`** (the official script uses `C:\msys64`) |
| **Zig 0.17.0** (`zig cc`) | compile the game code on the player's PC | installed: `build/zig` (hash checked) |
| Dear ImGui, VMA, SMAA, FSR1 | UI and post-processing | already in `third_party/` |
| PyInstaller | package generator and randomizer | not installed (release only) |

### What I verified ✅
- `make build/lasrecomp.exe` → **compiles** (12 MB) with clang 23.
- The app **opens** with Vulkan on the RTX 3070 Ti and shows the "Game Files" screen (asks for the v1.0.0 dump).
- `test_simd.py`: **1,048,640 encodings** with validity identical to Unicorn's; **12,000 cases** executed, **0 failures**.

### Problems found in the project (not caused by the environment)
1. **Makefile**: `all: $(EXE) $(if $(GEN_SRC),$(GAMELIB))`. Without `generated/`, `GEN_SRC` is `" "`
   (two empty `wildcard`s + a space), and GNU make treats that as true. It tries to link an empty `lasgame.dll`
   and fails. **Workaround:** `make build/lasrecomp.exe` (or `$(strip $(GEN_SRC))` in the Makefile).
2. **`tools/test_simd_harness.c`** is outdated: it declares `fnprof_hit(uint64_t)`, but `cpu.h` changed to
   3 arguments. I ran it on a fixed copy, outside the repository.
3. **`test_translate.sh`** depends on commit `652e234`, which **does not exist in the public (squashed) history**.
4. The docs warn: **do not run the window under MSYS `timeout`**, because it hangs. Use Python/PowerShell for window tests.

### How to build here
```bash
export PATH="/d/msys64/ucrt64/bin:/d/msys64/usr/bin:$PATH"
cd /d/Dev/REA/ref/LASRecomp-main/LASRecomp-main
make -j12 build/lasrecomp.exe          # runtime/app (no game)
# with your dump in extracted/:  make gen && make -j12   → generated/ + build/lasgame.dll
# run: PATH with D:\msys64\ucrt64\bin (DLLs)  →  build\lasrecomp.exe
```
Copy with git history: `D:\Dev\REA\ref\LASRecomp-git` (LF, `autocrlf=false`).

---

## 8. If we were to do something similar: lessons

1. **Pick a target with metadata**: `.eh_frame` + SDK symbols are what made function discovery and
   HLE feasible. A binary without symbols multiplies the work.
2. **Static recompilation is feasible when the code is fixed** (no JIT, no self-modifying code). The
   real difficulty is in: jump tables (resolved by emulation), indirect calls (dispatch with a cache), and FP/SIMD.
3. **Oracle first**: before writing the lifter, have Unicorn as a reference and differential tests.
   They make sure the AI does not just "think" it got it right.
4. **Reimplement the API, not the hardware**: HLE of NVN and the services instead of emulating the GPU/kernel.
5. **Self-checking patches** (check the original word) and **debug hooks via environment
   variables** from day 1; automatic screenshots for visual validation.
6. **Legal by architecture**: distribute only the generator; the game code is born on the machine of whoever owns the game.
7. **With our setup** (Claude orchestrating + local models + REA): REA/Ghidra comes in at the **understanding the
   binary** stage (finding functions, structs, who calls what), which here was done with `fnprof`/`ADDF_MATCH`/`sym.py`.
   The local model is for closed, verifiable cards (tests, tables, triage of draw logs). Lifter,
   shader translator, and architecture decisions stay with Claude, always with differential tests as the contract.
