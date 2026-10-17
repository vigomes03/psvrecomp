# PSV Recomp: Pokémon Violet static recompilation (study workspace)

A personal research workspace that **statically recompiles Pokémon Violet** (Nintendo Switch) into a native Windows
application, following the approach of [LAS Recomp](https://github.com/peiikai/LASRecomp), and uses the result to
study how a modern AAA game is built.

> **Personal use only.** This repository contains **no game code, assets, ROMs, or keys**. To use it you need your own
> cartridge dump and the keys from your own console. Nothing derived from the game is distributed. See
> [Legal and privacy](#legal-and-privacy).

Why the project exists and what success looks like: [IDEA.md](IDEA.md).

## Goals
1. **Native port (PSV Recomp):** translate the game's ARM64 code to C ahead of time, run it on a C re-implementation
   of the Switch OS, and render through an NVN layer built on Vulkan.
2. **A real app:** settings menu, launcher, frame pacing, resolution scaling, upscaling, and anti-aliasing.
3. **Study:** document the engine, file formats, rendering pipeline, and gameplay systems, with sources.

## How it works
| Layer | Approach | Where |
|---|---|---|
| CPU | All ARM64 code (`main`, `subsdk*`, `sdk`) is translated **once** to C and compiled to x86-64 (`pvgame.dll`). No JIT or interpreter at runtime. | `psvrecomp/recomp/` |
| OS (Horizon) | High-level emulation in C: loader, kernel/SVCs, IPC, services (`fs`, `hid`, `audren`, ...). | `psvrecomp/runtime/` |
| GPU | NVN calls served by a Vulkan backend; Maxwell shaders translated to GLSL/SPIR-V at runtime. | `psvrecomp/runtime/nvn/` |
| App | SDL3 window, ImGui overlay menu, `psvrecomp.ini` settings, crash report, safe start. | `psvrecomp/runtime/ui/` |

## Status
The [active roadmap](docs/roadmap/README.md) separates established historical results, observed features and
open acceptance tasks. Revision: 2026-10-17; no runtime experiment was rerun for this documentation rewrite.
- Historical v4.0.0 headless frame/time-limit evidence: run_id=7adc0390c2.
- Historical 600-second copied-save open-world route: run_id=c6a80b10d8; not full-game stability.
- The latest recorded headless host build failed: run_id=648a2fa61b; fresh baseline is the next task.
- Overlay/ini/safe-start observations exist; launcher and full app acceptance remain open.
- The focused study path is archive/scene tracing followed by a reversible custom-platform experiment.
- The old roadmap is [archived](docs/roadmap/archive/README.md), not another active work queue.

Primary target is game version **4.0.0** (base 1.0.0 + update). 1.0.0 is kept as a comparison build.

## Requirements
- **Windows 10/11**, a Vulkan 1.3 GPU, 32 GB RAM recommended (recompiling ~271k functions is memory and CPU heavy),
  and tens of GB of free disk for dumps and generated code.
- **Your own content** in `roms/` (ignored by git):
  - `roms\Pokémon Violet.xci` (base game dump);
  - `roms\Pokémon Violet Update V4.0.0.nsp` (update dump);
  - `keys\game.keys` from your own console.
- **Toolchain** (paths are currently hard-coded for this machine; adjust the scripts if yours differ):
  - [MSYS2](https://www.msys2.org/) UCRT64 at `D:\msys64` with clang, lld, SDL3, Vulkan headers/loader, shaderc,
    and vulkan-memory-allocator;
  - `hactool` at `D:\Tools\hactool\hactool.exe` and `hactoolnet` at `D:\Tools\hactoolnet\` (dump extraction);
  - Python 3.12 venv at `psvrecomp\recomp\venv` with `capstone`, `unicorn`, and `lz4`;
  - a local copy of LAS Recomp under `ref\LASRecomp-main\` (the Vulkan build reuses its VMA source).
- The workspace is expected at **`D:\Dev\REA`**; several scripts use that absolute path.

Full environment notes, verified versions, and known traps: [docs/environment.md](docs/environment.md).

## Quick start
Shortcuts live in `scripts/` and resolve project paths from the repository root, even when launched elsewhere.
Extraction scripts retain their existing overwrite guards. Recompilation asks for confirmation unless `--yes` is given.

| Step | Command | Result |
|---|---|---|
| 1. Extract the base game | `scripts\extract_base.cmd` | `dumps\base\` (secure partition, ExeFS, RomFS) |
| 2. Apply the 4.0.0 update | `scripts\extract_update_v400.cmd` | `dumps\v400\` |
| 3. Recompile | `scripts\recompile_v400.cmd` (add `--yes` to skip the prompt) | generated C and objects in `lab\gen-v400\` |
| 4. Build and smoke test | `scripts\build_and_test_v400.cmd` | Vulkan host + `pvgame.dll`, 30-second automated boot in `lab\host-test-v400\` |
| 5. Play | `scripts\launch_game.cmd [host_dir] [version] [seconds] [monitor]` | game window; log in `<host_dir>\window.log` |

The extraction scripts never print logs that may contain key material.

### Controls
| Input | Keyboard | Gamepad |
|---|---|---|
| Left stick / D-pad | WASD / arrow keys | sticks / D-pad |
| A / B / X / Y | K or Space / J / I / L | by position (Switch layout) |
| L / R, ZL / ZR | Q / E, 1 / 3 | shoulders / triggers |
| + / - | Enter / Backspace | Start / Back |
| Right stick | numpad 8/4/5/6 | right stick |
| Settings menu | F1 or Esc | Home, or Back + Start |

The menu has Controls, Video (monitor, fullscreen, VSync, FPS counter, scale, FSR1, SMAA), Audio, and Quit. Settings
are saved in `psvrecomp.ini` next to the executable. If the game crashes during startup or right after a settings
change, the next start moves the ini to `psvrecomp.ini.crashed` and uses defaults.

### Development builds
```bash
# Vulkan runtime -> lab/host-vk/pvhost.exe
cd psvrecomp/recomp && bash build_host.sh /d/Dev/REA/lab/host-vk vulkan
# The only accepted proof that it builds/boots (records a run_id in work/evidence/gates.jsonl)
python tools/verify/gates.py run host --version v400
# Automated run with scripted input, logs and screenshots
bash tools/verify/run_auto.sh <seconds> <name> [VAR=value ...]
```
Tests that do not need the game:
```bash
cd psvrecomp/recomp
export PATH="/d/msys64/ucrt64/bin:$PATH"   # only for this command
venv/Scripts/python.exe test_simd.py --encodings 400 --cases 30 --seed 1 --jobs 8
python ../../tools/verify/test_glsl_slice.py
python ../../tools/verify/test_gates.py
```
Diagnostic environment variables (`PVR_*`, `LARECOMP_*`) are documented in
[psvrecomp/README.md](psvrecomp/README.md).

## Repository layout
```
D:\Dev\REA\
├─ README.md / IDEA.md        this file / project goals
├─ CLAUDE.md / AGENTS.md      rules for Claude and every other agent
├─ scripts/                   CMD shortcuts (extract, recompile, build+test, launch)
├─ psvrecomp/                 the recompiler (recomp/) and the native runtime (runtime/)
├─ tools/rea/                 reverse engineering helpers (REA/Ghidra harness, crash and profiling reports)
├─ tools/verify/              gates.py (evidence), run_auto.sh, tests, pre-commit hook
├─ tools/workers/             local model workers (code, translation)
├─ docs/                      findings, guides, roadmap, pipeline log
├─ work/                      work cards, worker context, evidence logs (no game content)
├─ .agents/skills/            versioned agent skills for this workspace
├─ roms/ keys/ dumps/         your private content                [ignored]
├─ lab/                       builds, logs, screenshots, reports   [ignored]
└─ ref/                       third-party reference projects       [ignored]
```

## How development works
- **Claude orchestrates, local models execute.** Work is split into small cards (`work/cards/`) with acceptance
  checks a script can run; local models (Ollama) produce the output through harnesses in `tools/workers/` and
  `tools/rea/`; Claude verifies every delivery. Rules: [CLAUDE.md](CLAUDE.md).
- **Evidence, not claims.** `tools/verify/gates.py` runs the real command and records hashes, exit codes, and boot
  stage. The pre-commit hook rejects docs that claim completion without a valid `run_id`.
- **Every card is logged** in [docs/pipeline-log.md](docs/pipeline-log.md).
- **Language:** all documentation, code, and comments are in English.

## Documentation
| Document | Content |
|---|---|
| [docs/README.md](docs/README.md) | Index of findings and guides |
| [docs/roadmap/README.md](docs/roadmap/README.md) | Active baseline/app/scene/platform tracks, evidence, backlog and old-phase mapping |
| [docs/lasrecomp-study.md](docs/lasrecomp-study.md) | How LAS Recomp was made and what we reuse |
| [docs/rea-local-agent.md](docs/rea-local-agent.md) | REA/Ghidra + local model setup |
| [psvrecomp/README.md](psvrecomp/README.md) | Runtime details and diagnostic variables |

## Legal and privacy
- Use only a dump of a cartridge you own and keys from your own console. Never download ROMs, keys, or firmware.
- ROMs, keys, dumps, generated code, and Ghidra/REA output on the game stay in git-ignored folders and are never
  committed, uploaded, or shared.
- Docs may describe **how** something works; they must not contain game code, assets, or text.
- Pokémon is a trademark of Nintendo, Creatures Inc., and GAME FREAK inc. This project is not affiliated with or
  endorsed by them.

## Credits and licenses
- [LAS Recomp](https://github.com/peiikai/LASRecomp) by Peiikai (MIT): the recompiler and runtime this project forked;
  see `psvrecomp/third_party/LICENSE-LASRecomp.txt`.
- [Dear ImGui](https://github.com/ocornut/imgui) (MIT), [SMAA](https://github.com/iryoku/smaa) (MIT), Baloo 2 font
  (SIL OFL): under `psvrecomp/third_party/`.
- Eden (GPL-3): used only as a behavioral and visual reference; no code is copied.
- [REA](https://github.com/morluto/rea) and [Ghidra](https://ghidra-sre.org/): reverse engineering tooling.
