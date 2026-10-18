# Direct Ghidra call-site probe (synthetic control)

This is a narrow verification helper, **not** evidence of a real game loader/resource call chain.
It does not modify REA's Windows adapter or make that adapter accept raw ARM64. The accepted experiment
uses only our own clang-assembled ARM64 fixture, not dumps, saves, generated game code or an existing private project.

## Run the actual controls

From `D:/Dev/REA`, using the existing verification Python environment:

```sh
python tools/verify/test_ghidra_call_probe.py
```

Prerequisites already present in the tested environment:

- `D:/msys64/ucrt64/bin/clang.exe`, cross-assembling with `--target=aarch64-none-elf`.
- `D:/Tools/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat` and its existing Java runtime.
- Windows `cmd`/`taskkill`; `psutil` for the timeout test's owned-process check. No packages are installed by the tests.

`build_probe_fixture.py` assembles our fixture and reads the object section/symbol table using `elf_min.py`.
The latter is deliberately only a reader for our compiler's output, not a hardened general-purpose ELF parser.
`ghidra_call_probe.py` runs the installed analyzer with BinaryLoader and `AARCH64:LE:64:v8A`, disables broad
analysis, and invokes `CallProbeScript.java`. The script disassembles the requested instruction and locates or
creates the direct target function. A generated function name is not a recovered original symbol or proof of
an automatically discovered function corpus. Indirect/unresolved calls are outside this experiment.

## Accepted real controls

The six tests check a known BL/target/function, a non-call MOV, a missing input, a missing post-script,
an unaligned address, and a real subprocess timeout. Only the script-name argument is replaced for the
missing-script fault; Ghidra itself is never mocked. Import success without actual metadata is rejected.

Accepted exact-command delegated receipt: `lab/orchestration/W30-exact-controls.stream.jsonl`.
Actual tool output: six tests passed in 10.337 seconds, no permission denials. Artifacts:
`lab/analysis-probe-tests/controls-75012ab6e6/`.

- Positive: site `0x100004`, `bl`, target `0x100010`, function `FUN_00100010`, actual image base `0x100000`.
- Negative: site `0x100000`, `mov`, `is_call=false`, no target/function.
- Timeout: 0.5-second limit, measured return 0.65 seconds; no owned JVM remaining after the control.
- Native stdout, stderr, application/script logs and returned JSON are retained under each control directory.
  Projects have fresh owned UUID names and are removed only after their process exits. Raw outputs stay ignored.
- Fresh independent source review: `lab/orchestration/W30-independent-review-isolated.json`, no blocking findings.
  Peak RAM/VRAM was not measured; this was a headless synthetic experiment, not a game/performance gate.

## Lessons and boundaries

- BinaryLoader's block base and program image base are different. The installed `Base-src.zip` implementation
  creates a program at zero even when `loader-baseAddr` places a block elsewhere. Import at zero, genuinely
  rebase the program before decoding, verify its memory start, and report the observed image base.
- A global callee in an unlinked ARM64 object can leave a CALL26 relocation and zero branch immediate.
  Use the fixture's local callee so clang resolves the branch before extracting raw `.text`; the independent
  symbol-table target comparison caught the original self-call. Do not treat unrelocated `.text` as linked code.
- Killing only `cmd.exe` on timeout can leave the JVM holding captured streams open. Kill only the owned PID
  tree with `taskkill /T`, reap it, retain logs, and fail the operation. Never kill all Java processes by name.
- The user authorized reading/executing only the exact existing Ghidra installation, not editing/upgrading it
  or browsing other tool directories. Keep all authored scripts, fixtures and analysis outputs in REA.
- For delegated execution, prefer the one reviewed test command with its exact allow rule. The exploratory
  W30 retry hit the turn limit after repeated denied compound/discovery commands; those results were not accepted.
  Do not broaden permissions or retry denied operations through alternate wrappers. Read-only review sessions
  should have no tools/MCP servers: pass the supplied source as data, without unrelated connector discovery.
- Function/call-chain analysis of an actual observed guest path is still a separate R-01 acceptance step.
  Do not point this experiment at a private target or claim scene-load understanding from these controls.

## Separate scoped-function entry

[Scoped candidate-function analysis](SCOPED_FUNCTIONS.md) uses a different, independently tested post-script
for approved local R-01 experiments. It does not turn the default W30 fixture experiment into real-game proof.
Candidate bounds, entry-flow uncertainty, private outputs and decompiler warnings remain explicit.
