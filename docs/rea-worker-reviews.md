# Claude Reviews: Local REA Worker

Gabarito do Claude (`whoami.exe`): `LookupAccountSidW` is called at 0x140003d24, within `FUN_140003bc0`
(ev_8e65ba5e…). This function enables `SeDebugPrivilege` and resolves the SID `*param_1` to `DOMÍNIO\nome`.
Callers: `FUN_140003498` (call at 0x14000377c) and `FUN_140003b3c` (call at 0x140003b64), ev_3cb3d430….

| run | executor | REA calls | time | verdict | reason |
|---|---|---|---|---|---|
| 1 | delegate_task (Hermes subagent, qwen3-coder-64k) | 0 | 2m10 | REJECTED | 100% fabricated report (main/TokenGroups/malloc, "10 call sites") |
| 2 | rea_worker v1 | 13 | 5m30 | REJECTED | honest, but followed the string in .rdata; "no references" citing wrong xrefs |
| 3 | rea_worker v2 (+callers) | 7 | 5m28 | ACCEPTED with correction | correct function and verbatim code; invented caller `FUN_14000377c` (was call address) |
| 4 | rea_worker v3 (+symbol checking) | 7 | 7m58 | ACCEPTED with reservations | correct function + 2 correct callers; cited ids = decompile (not xrefs); empty code section |

## Lessons from Code Cards (W01/W02)
- qwen confuses `bits(w, lo, n)` with "high bit": in the card field table, write the **ready call** (`bits(w, 16, 5)`), not "bits 20:16".
- On a retry it "improves" parts that were already correct (changed type `Insn('op')`). In the retry card, list what **cannot** change,
  and the acceptance test should check the interface (type/signature), not just the text or result.
- Differential test against oracle (Unicorn) caught the error that quick reading would miss.

## W20 glsl_slice.py (15/10) — REJECTED 2x
- t1: did not print anything (pc read in wrong order when stepping back; search started before the instruction itself — part
  of this was a card error, which contradicted the test). t2: `uses` included the register itself and recursion started from line 0.
- Claude rewrote (`tools/rea/glsl_slice.py`, test `tools/verify/test_glsl_slice.py` PASS). Attempts in
  `lab/arquivo/w20/`; score: `gates.py note --verdict FALSE`.
- Lesson: tool with flow analysis (step back with predicates) is core work; qwen does better on cards with fixed input/output and value table.
  - Lesson: cards with fixed input/output and value table.
