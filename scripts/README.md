# Windows shortcuts

These wrappers moved from the repository root to `scripts/`. Double-click them, or run from the root:

| Command | Purpose |
|---|---|
| `scripts\extract_base.cmd` | Extract the user's own base cartridge into `dumps/base/` |
| `scripts\extract_update_v400.cmd` | Apply the user's own update; outputs `dumps/v400/` |
| `scripts\recompile_v400.cmd` | Regenerate/compile v4.0.0 modules; asks for confirmation (`--yes` skips it) |
| `scripts\build_and_test_v400.cmd` | Build an isolated Vulkan host and run the existing 30-second boot command |
| `scripts\launch_game.cmd [host_dir] [version] [seconds] [monitor]` | Forward arguments to the manual-play wrapper |

All accept `--help` without starting their workload. Paths to repository content resolve from the script's parent,
not the caller's current directory. Tool installations and Bash commands still target this machine's `D:/Dev/REA`
and `D:/msys64`; this move is not a general portability rewrite.

Extraction uses UTF-8 console decoding for the existing accented file names. Extraction diagnostics can contain
key material: do not print, commit or share them. No content is downloaded. Existing overwrite guards remain.
The update wrapper uses the recompilation Python environment and verifies required extensionless modules
`main`, `sdk`, `subsdk0`; a missing module or segment hash mismatch stops it.

## Regression checks

From the repository root on Windows:

- `python tools/verify/test_shortcuts.py -v`
- `python tools/verify/test_nso_verify.py -v`
- `python tools/verify/test_gates.py`

The wrapper tests copy scripts into disposable paths containing spaces under ignored `lab/shortcut-tests/`.
They exercise CMD help/root resolution, prompt accept/decline, a running-game refusal, UTF-8 paths, launcher argument
and exit-code forwarding, and the actual NSO verification block on synthetic extensionless modules.
Build commands are replaced by explicitly failing fixture commands; extraction/key-handling stages are not run.
The NSO tests use synthetic uncompressed segments and require `psvrecomp/recomp/venv/Scripts/python.exe` with lz4.

These checks validate wrapper behavior, not a real extraction, recompilation, gameplay session or a new baseline.
The [active roadmap](../docs/roadmap/README.md) still owns current-build acceptance.
