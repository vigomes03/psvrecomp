# W31 — Bind the B-03 crash to its native/guest call metadata

## Scope

Resume the recorded B-03 blocker without guessing a runtime fix. Use existing deterministic verification tools
and metadata only; retain private disassembly and raw images under ignored lab/. No game code/pseudocode goes
to a cloud worker. Do not load Qwen alongside the game after the observed memory pressure. No installation,
global configuration changes, broad rare-crash investigation, original-save writes, commits or pushes.

## Inputs and existing interfaces

- Failed window record run_id=e5b2041956 in work/evidence/gates.jsonl.
- tools/rea/crash_report.py with --host-dir D:/Dev/REA/lab/host-vk-auto.
- tools/rea/cpuprof_report.py: symbols(path), image_base(path); verify output hashes before using its nearest-symbol lookup.
- psvrecomp/recomp/nso.py: Nso(path).image, .build_id and .text. Use the existing project interpreter at
  psvrecomp/recomp/venv/Scripts/python.exe; the desktop interpreter lacks its LZ4/Capstone dependencies.
- Existing project Capstone API: Cs(CS_ARCH_ARM64, CS_MODE_ARM), detail=True, ARM64_OP_IMM.
- tools/verify/gates.py: host_build_provenance, save_manifest, prepare_window_save, window_environment.

## Acceptance and boundaries

1. Current host and DLL hashes must equal the failure record before symbolization; retain the checks.
2. Resolve the fault RVA inside a bounded native text-symbol interval, not an unchecked nearest-symbol name.
3. Compare the existing raw image hash with the current NSO loader's decompressed image and record its build id.
4. Decode only the recorded guest LR minus four. Require a direct BL whose target matches the compiled fault
   symbol; independently compare its containing guest-symbol interval with the next native stack frame.
5. Attempt one 30-second replay with no retry wrapper: fresh copied binaries/settings/save, exact recorded input,
   monitor 2 and dummy audio, owned-process timeout. Check source save unchanged and binary hashes again.
6. Preserve all receipts. A clean short diagnostic is not a B-03 gameplay gate or a fix. No invented gate entries.

## Execution receipt

The verification-infrastructure exception covers parent-run binding/correlation and the one-off isolated
replay; no product code changed. Receipts: lab/reports/W31-crash-triage/. Review and limits:
[crash triage note](../../docs/roadmap/crash-triage-2026-10-18.md). Root cause and B-03 acceptance remain open.
