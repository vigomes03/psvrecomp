# W30 — Bounded direct-Ghidra call-site probe on synthetic ARM64

## Owner and scope

Claude Code owns this narrow R-01 verification-infrastructure slice in D:/Dev/REA. Parent reviews the delivery.
The roadmap allows independent read-only R work while B-03 is blocked; B-04 now has recovery/reload evidence
7ea127f858 and d6946b460e. B-03 pre-battle e5b2041956 failed its first attempt. Do not work on that crash here.
Preserve all existing dirty files. No commit, push, reset, stash, installation, other-project/config edits or
unrelated process kills. Repository English, final summary PT-BR. Do not read/write external agent memory.

## Narrow installation authorization (user approved)

The user explicitly approved reading and executing the existing Ghidra installation at
D:/Tools/ghidra_12.1.4_PUBLIC. The parent preflight read its application.properties through the delegated session
and executed the actual headless launcher: version 12.1.4 and real usage output, no permission denials.
The launcher is D:/Tools/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat. No need to rediscover D:/Tools or inspect
other installations. Only this exact directory is added to the session. No writes/edits/installation/upgrade there.
Keep ALL owned outputs inside D:/Dev/REA. Existing global configuration remains unchanged. This supersedes the
previous installation-access blocker, not the rest of the task's scope or stop-on-denial rule.

## Task: one tested tool, not a full roadmap session

Build a minimal reusable direct-Ghidra post-script/runner that verifies one ARM64 call-site/function relationship.
FIRST make a failing synthetic positive/negative control, THEN provide the smallest script/runner that satisfies it.
Exercise the REAL installed Ghidra headless process on our own synthetic ARM64 instructions, not a mocked provider.
Do not return only a plan or ask to start the already-authorized local tests. Runtime duration is not API token cost;
respect the actual CLI cap and stop on a real blocker, not speculative expense.

Read existing APIs first. Installed Ghidra has already imported a raw image directly (not through REA's Windows
adapter). Public reference source: ref/rea-main/rea-main/bridge/ghidra/ReaGhidraPrepareRaw.java and sibling scripts.
Ghidra installation: D:/Tools/ghidra_12.1.4_PUBLIC. JAVA_HOME is already set. Compiler used by this project:
D:/msys64/ucrt64/bin/clang.exe. Verify actual additional tools before using them; do not install anything.

## Output boundaries

Own ONLY new files under tools/analysis/ and tools/verify/test_ghidra_call_probe.py (additional narrowly named
probe support under tools/verify/ if essential). Keep fixture binaries/projects/stdout/reports in ignored
lab/analysis-probe-tests/. Do not change runtime, gates.py, upstream ref/ code or the existing private Ghidra project.
Do not change source binaries. Do not access dumps, keys, saved games, generated game C, or private game pseudocode.
No game launch, private-target analysis, or screenshots in this slice. Only public bridge source + OUR synthetic fixture.

## Required behavior and controls

- Query a supplied function entry/call-site in an AARCH64:LE:64:v8A program; report descriptive metadata:
  language, image base, requested entry/site, whether instructions/function exist, call classification and targets.
- A small synthetic fixture contains a known BL call to a known local callee, plus a non-call instruction.
  Generate it using the verified assembler/toolchain or validate instruction encodings against that toolchain.
- Positive control: real Ghidra identifies the call and its expected target/function metadata.
- Negative control: selecting a non-call address is rejected as a call relationship, not labeled success.
- Fail closed on missing output, wrong language/base/target, invalid arguments, Ghidra/script errors or timeout.
  Do not declare success from process exit 0 or a generic Ghidra import marker alone.
- Keep analysis bounded: small fixture, explicit addresses, no broad automatic analysis, bounded subprocess timeout.
  Use a fresh owned project per test or explicit cleanup of only the test's own files. Retain failure logs.
- Use the expected production-boundary headless workflow, not a static source-string assertion or fake API response.
- The script must emit actual parseable metadata; do not fabricate results in Python or post-process failures into PASS.

This is a DIRECT Ghidra helper. REA's Windows adapter rejected raw ARM64. Do not bypass or modify its admission
guard, claim that REA now supports ARM64, or call synthetic evidence a real game loader/call chain. A later card
will correlate an actual observed guest call with this independently validated tool.

## Model/resources and permissions

Selected local worker remains qwen3.8:27b, only for suitable bounded tasks. No Devstral. Current free RAM was about
20 GiB with no Ollama model loaded; do not load a dense model blindly. Verification harness/diagnostic tooling is
a documented direct-execution exception, so Claude may handle this tightly scoped helper and its tests.
No concurrent game/GPU workload. Do not close applications or alter global settings to make the task fit.
If any tool command is denied, stop that operation and report the exact needed authorization; do not probe
alternate paths/wrappers or disable the sandbox. Python orchestration of the explicitly authorized compiler and
Ghidra tests is in scope, but not a means to evade a denied operation.

## Exit contract

Run the actual synthetic controls and report exact commands, artifacts, stdout paths, results and elapsed/resource
observations where measured. Wait for tests before returning; no unowned background jobs. If real execution is
blocked, report the precise blocker and retained partial files, without claiming R-01 closure. No editing roadmap
checkboxes or adding made-up gate records. Parent will review and advance the next bounded card.
