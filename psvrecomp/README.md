# PSV Recomp

Static recompilation of Pokémon Violet (v1.0.0 and the v4.0.0 update, [USER]'s cartridge and console), following the
process of LAS Recomp (Link's Awakening Switch). The application is called **PSV Recomp** (window title, `psvrecomp.log`,
`psvrecomp.ini`); the development binary is `pvhost.exe` + `pvgame.dll`.
Roadmap: [../docs/roadmap/README.md](../docs/roadmap/README.md). Rules: [../CLAUDE.md](../CLAUDE.md).
**Local use, nothing leaves this machine.**

## What it is (a recomp, not a CPU emulator)
- **CPU:** all of the game's ARM64 code (`main`, `subsdk*`, `sdk`) was translated **once, before running**, to C and
  compiled to x86-64 (`pvgame.dll`, ~271 thousand functions). There is no ARM interpreter or JIT at runtime.
- **System (Horizon OS):** rewritten in C (HLE): kernel/SVCs, IPC, services (`fs`, `hid`, `audren`...).
- **GPU:** the game's NVN calls are served by a Vulkan backend; the game's Maxwell shaders are translated to
  GLSL/SPIR-V **at runtime** (`runtime/nvn/maxwell/translate.c`), like an emulator does with the GPU.

## Folders
| Folder | Contents |
|---|---|
| `recomp/` | ARM64 → C recompiler (fork of LAS `tools/`: nso, analyze, lifter, simd_c, gen, layout, sym), differential tests, `build_host.sh` (runtime), `run_window.cmd` launcher |
| `runtime/` | native runtime: loader, kernel, IPC, services, `hle/` (input, nvn_boot...), `nvn/` (NVN layer), `nvn/vulkan/` (backend), `nvn/maxwell/` (shader translator), `platform/`, `ui/` |
| `third_party/` | `LICENSE-LASRecomp.txt` (MIT, Copyright (c) 2026 Peiikai), `smaa/` (SMAA, MIT, Jorge Jimenez et al.) |

Origin: `LASRecomp-main` (github.com/peiikai/LASRecomp, 10/14/2026). What was Zelda-specific was removed or became a neutral
stub (`runtime/pv_zelda_stubs.c`). Recompiler changes relative to the original: empty `patches.py`, harness path
in `test_simd.py`, `fnprof_hit` signature in `test_simd_harness.c`. The history of every runtime change
is in `../docs/pipeline-log.md`.

## Run
```bash
# runtime build (Vulkan) -> D:/Dev/REA/lab/host-vk/pvhost.exe
cd "psvrecomp/recomp" && bash build_host.sh /d/Dev/REA/lab/host-vk vulkan
# build/boot proof (the only accepted proof, see CLAUDE.md)
python tools/verify/gates.py run host --version v400
```
- **Play by hand:** double-click `recomp/run_window.cmd` (no time limit, opens on monitor 2; keyboard WASD/arrows,
  K or Space = A, J = B, I = X, L = Y, or an Xbox/PS/Switch Pro controller). Log in `lab/host-vk/window.log`.
- **Pipeline (Claude):** `bash tools/verify/run_auto.sh <seconds> <name> [VAR=value ...]` — automatic input,
  log `lab/host-vk/<name>.log`, frames with `LARECOMP_SCREENSHOT_EVERY/FROM`.

## Extract your own Switch content
- From the workspace root, `scripts\extract_base.cmd` extracts `roms\Pokémon Violet.xci` into `dumps\base\`.
- Then, `scripts\extract_update_v400.cmd` applies `roms\Pokémon Violet Update V4.0.0.nsp` to the base and writes
  `dumps\v400\`. It uses `hactool` for ExeFS and `hactoolnet` for the BKTR update RomFS.
- Both scripts refuse to overwrite existing dumps, require `keys\game.keys`, and do not print logs that may contain key
  data. ROMs, keys, dumps, and extraction logs remain ignored by Git.

## Shortcuts in scripts/
| Script | Purpose |
|---|---|
| `scripts\extract_base.cmd` | Extract the base XCI into `dumps\base\`. |
| `scripts\extract_update_v400.cmd` | Extract the v4.0.0 NSP and apply it to produce `dumps\v400\`. |
| `scripts\recompile_v400.cmd` | Generate C and compile all v4.0.0 modules into `lab\gen-v400\`. This is CPU and disk intensive. |
| `scripts\build_and_test_v400.cmd` | Build an isolated Vulkan host, link `pvgame.dll`, and run a 30-second boot test in `lab\host-test-v400\`. |
| `scripts\launch_game.cmd` | Start the manual-play launcher. |

## Diagnostic tools (environment variables, all off by default)
| Variable | What it does |
|---|---|
| `LARECOMP_TRACE_SAVE=1` | Opt-in host save-mount create/read/write/flush/rename/commit trace. Rebuild the Vulkan host before use; this is not an atomic-save implementation. |
| `LARECOMP_DEBUG_FRAME=<n>` / `PVR_DEBUG_ON=<w>x<h>/<fmt>` / `PVR_DEBUG_ON_COPY=<w>x<h>` | lists every draw of a frame (by number, or triggered when the scene uses a given texture/copy) and saves each pass |
| `PVR_DIAG_SAVETEX=<w>` + `PVR_DIAG_SAVETEX_FS=<fs>` | saves the textures read by a shader's draws |
| `PVR_DBG_FS=<fs,...>` `PVR_DBG_PC` `PVR_DBG_REG` `PVR_DBG_RT` (+`SIGNED/FRACT/UINT`) | paints shader output white or shows a register |
| `PVR_DBG_SREF=<from>:<to>` `PVR_DBG_CBFILL=<k>:<word>` `PVR_WATCH=<addr>` | swaps a stencil reference / fills a cbuf / watches who writes to an address |
| `PVR_LOG_COPIES` `PVR_SAVE_COPY=<w>x<h>` `PVR_LOG_TEXADDR=<addr>` | texture/buffer copies, saved source, textures at an address |
| `PVR_NO_BRA_CC` `PVR_NO_COPY_WRITEBACK` `PVR_NO_QUADSWAP` `PVR_NO_STENCIL_VIEW` | A/B: turns off one fix for comparison |
| `PVR_NVN_MISSING` `PVR_DIAG_UNKNOWN` `PVR_DUMP_THREADS` `PVR_SYM_AT` | missing NVN functions, unknown Maxwell instructions, threads, symbols |
| `PVR_CPUPROF=<from_s>:<to_s>` | samples the CPU of the game threads (~1 ms) and writes `build/cpuprof.txt`; report: `tools/rea/cpuprof_report.py build/cpuprof.txt pvgame.dll pvhost.exe` |
| `LARECOMP_VK_PROF=1` | render thread time by category, GPU busy, and GPU waits by site (`waits by site`, RVA for `addr2line`) |
| `PVR_GAME60=1` | (experimental, v4.0.0 only) turns on the game's own 60 fps mode: zeroes the "interval-1" byte of the video config (read by 0x7002b7a898); the speed stays correct (walking test same as at 30 fps) |
| `PVR_FORCE_INTERVAL=<n>` | (experiment) NVN stores interval n instead of the one the game asked for |
| `PVR_FRAMEPACE=0` / `PVR_FPS_CAP=<fps>` | turns off the presentation limiter (the game speeds up in light scenes) / uses another rate instead of 60/interval (Violet asks for interval 2 = 30 fps) |
| `PVR_XFB_SCRATCH=0` / `PVR_XFB_OWN_PASS=0` | A/B: transform feedback (characters) writes directly to guest memory again / in the normal pass |
| `PVR_SUBMIT=list` | A/B: one submission per command list (the default follows NVN: submits on Flush/Finish/present) |
| `PVR_XFB_NOSTORE=1` | (measurement, breaks the image) xfb shaders without the writes |
| `PVR_OCCLUSION_ZERO=1` | A/B: the occlusion query reports 0 pixels again (the game hides the character in the open world) |
| (always on) `[frametime]` in the log | every 10 s and at the end: average, p50/p95/p99, max, 1% low, spikes >1.5x the period, and the cause (shader, upload, gpu, game). `PVR_FRAMETIME_CSV=<file>`: one row per frame; `PVR_FRAMETIME_EVERY=<s>` changes the interval. "work" = time of the presenting thread, not of the whole game |
| (always) crash report | fatal error or exception: the whole log is copied to `<log folder>\crashes\crash_<date>_<time>.log` and a box with the cause appears (not in timed runs, `PVR_RUN_SECONDS` > 0, nor with `PVR_NO_CRASH_BOX=1`). Read it with: `python tools/rea/crash_report.py <log>` (names the game functions, `f_<address>`, with the same build) |
| `PVR_TEST_CRASH=<frame>` | triggers a fatal error at that frame (crash report test) |
| `PVR_SWKBD_TEXT=<text>` | keyboard answer (name) without a window; when playing without it a text box appears in front of the game; in timed runs it uses the game's suggestion or "[USER]" |
| `PVR_SUBS=<1..64>` | how many in-flight submissions the backend uses (default 64; LAS used 8) — performance A/B |

Usage details and traps: skill `switch-static-recompilation` (reference `vulkan-backend.md`).

## Tests (no game needed)
```bash
cd "psvrecomp/recomp"
export PATH="/d/msys64/ucrt64/bin:$PATH"   # clang (only in this command)
venv/Scripts/python.exe test_simd.py --encodings 400 --cases 30 --seed 1 --jobs 8
python ../../tools/verify/test_glsl_slice.py
```
