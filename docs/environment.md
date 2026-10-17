# REA workspace environment (verified on 10/14/2026)

Machine: Windows 11, RTX 3070 Ti 8 GB, 32 GB RAM, C: almost full, so **everything goes on D:**.

## Installed tools

| Tool | Path | Purpose | Verification |
|---|---|---|---|
| REA (snapshot of `main`, v6.4.0) | `D:\Dev\REA\ref\rea-main\rea-main` | RE via CLI/MCP | `rea doctor --provider ghidra` green |
| REA's Windows native addon | `ref\rea-main\rea-main\native\windows\build` | required for Ghidra on Windows | `npm run verify:windows-native:artifact` |
| Ghidra 12.1.4 | `D:\Tools\ghidra_12.1.4_PUBLIC` (`GHIDRA_INSTALL_DIR`) | decompilation | ✅ |
| Temurin JDK 21 | `D:\Tools\jdk-21.0.12.1+1` (`JAVA_HOME`) | Ghidra | ✅ |
| MinGW-w64 (WinLibs GCC 16.2) | `D:\Tools\mingw64` | build the REA addon | ✅ |
| MSYS2 UCRT64 (clang 23, lld, make, SDL3, FFmpeg, Vulkan, shaderc, SPIRV-Tools, gdb) | `D:\msys64` | build LASRecomp / native code | ✅ `lasrecomp.exe` builds and opens |
| Python 3.12 (uv) + unicorn 2.1.4, capstone 5.0.9, lz4 | `ref\LASRecomp-main\...\tools\venv` | lifter / differential tests | `test_simd.py` logged in the 10/14 pipeline (0 failures) |
| Zig 0.17.0 | `ref\LASRecomp-main\...\build\zig` | `zig cc` | hash logged in `docs/pipeline-log.md` |
| hactool (SciresM, `1d64a83`, built from source with WinLibs) | `D:\Tools\hactool\hactool.exe` (source in `D:\Tools\src\hactool`) | read/extract XCI/NCA/RomFS | ✅ reads the XCI header without keys |
| Ollama + `devstral:24b` (since 10/17; before: `qwen3-coder-64k`) | local service `127.0.0.1:11434` | local worker | ✅ |

## Rebuild REA's native addon (if `native/windows/src` changes)
The npm 6.4.0 artifact **does not work** for this snapshot (`privateBridgeDescriptorAccess`).
1. PATH with `D:\Tools\mingw64\bin` first; there are copies `x86_64-w64-mingw32-dlltool.exe` and `x86_64-w64-mingw32-as.exe`.
2. `node --import <file that does Object.defineProperty(process,'platform',{value:'linux'})> scripts/build-windows-native.mjs`
3. `npm run verify:windows-native:artifact`

## Known traps
- **`TMP=/tmp` breaks REA.** With MSYS2 first on PATH, `TMP`/`TEMP` become `/tmp`, and the native self-test fails
  (`Create private object relative to its admitted parent`). `tools/rea/rea.sh` and `rea_worker.py` already force the Windows Temp.
- **Do not leave MSYS2 permanently on the terminal PATH**: export it only in the command that compiles.
- Full REA MCP = 207 tools (~220k tokens). In Hermes, `tools.include` with 21 tools + `compact` (~8k).
- Each REA CLI call re-imports into Ghidra (~20 s). The MCP session keeps Ghidra open.
- Test windows do not run under MSYS `timeout`: use Python `subprocess` with `timeout`.
- **MSYS2 `make` + native gcc loses `TMP`** (gcc: `Cannot create temporary file in C:\WINDOWS\`). For projects with a simple Makefile use WinLibs' `mingw32-make`, with `TMP` pointing to the Windows Temp.
- User variables set with `setx`: `GHIDRA_INSTALL_DIR`, `JAVA_HOME`.

## Windowed runtime (PSV Recomp, Vulkan) — verified on 10/15/2026
- Build: `bash "psvrecomp/recomp/build_host.sh" /d/Dev/REA/lab/host-vk vulkan` (clang/SDL3/shaderc from
  `D:\msys64\ucrt64`, only inside the command). Output `lab/host-vk/pvhost.exe` + `pvgame.dll`.
- `recomp/run_window.cmd` puts `D:\msys64\ucrt64\bin` on PATH (SDL3, shaderc, libstdc++ DLLs), clears the debug
  variables, and opens the window on monitor 2 (`PVR_DISPLAY`). `tools/verify/run_auto.sh` is the pipeline version.
- GPU: RTX 3070 Ti, Vulkan 1.3. Performance measured by [USER] on 10/15: 5-10 fps indoors, ~3 fps in open areas,
  CPU ~9 %, GPU almost idle (bottleneck on the CPU/synchronization side, not the card).

## NOT installed yet (next step for the Pokémon project)
- **Keys**: `prod.keys` (and `title.keys`, if any) dumped from **your** console with Lockpick_RCM →
  put them in `D:\Dev\REA\keys\` (ignored by git). Without them, hactool only reads the XCI header.
- ROM/dump: `roms/Pokémon Violet.xci`, 8 GB cartridge; partitions `update` (225 files, firmware), `logo`, `normal` (empty),
  `secure` (the game, encrypted NCAs). Extraction goes to `dumps/` (ignored).
- Game Freak asset formats (TRPAK/FlatBuffers etc.) still without a chosen tool.
