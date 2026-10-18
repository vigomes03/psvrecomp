# Evidence ledger

Status reference for the [active roadmap](README.md), reviewed 2026-10-17.
Source of gate records: `work/evidence/gates.jsonl`. These records were read; no new gate was run for this rewrite.
A historical hash identifies the old artifact, not the current file. Never edit evidence logs to match a plan.

## Established historical results

- [x] E-01 v4.0.0 pinned exefs and nonempty 30-file romfs: run_id=131ff828b2. Does not check every asset's integrity or prove a runtime layering implementation.
- [x] E-02 v4.0.0 headless frame markers and time limit in six attempts: run_id=7adc0390c2; reported 233,121 functions. Does not certify current builds or arbitrary kernel semantics.
- [x] E-03 Base headless frame markers and time limit in four attempts: run_id=db35401e31. Base remains a comparison target.
- [x] E-04 SIMD sample, 20,000 encodings / 159,968 cases with zero reported failures: run_id=782956f97a. The separate validity census is not exhaustive semantic testing.
- [x] E-05 Exclusive-pair sample, five codegen checks and 200 Unicorn cases: run_id=6efc28c218. Not a general concurrency proof.
- [x] E-06 New-game rendered scenes and input-driven scene changes: run_id=312d34de1a. Gate checks image metrics, not semantic identity of title/logo/character control.
- [x] E-07 Open-world copied-save route, 600 seconds, 17,227 frames, no recorded crash in first attempt: run_id=c6a80b10d8. Final windows 28.9 fps; not random exploration or full-game stability.

## Recorded observations, not new gate-backed closure

| Observation | Source | Boundary / next validation |
|---|---|---|
| Save persists across close/reopen | Pipeline log, user test 2026-10-15 | No guarantee of interruption recovery; B-04 |
| Keyboard input, audible sound, visible character name | Pipeline log, user confirmations 2026-10-15/16 | Not physical-controller, all sounds or Pokemon-rename coverage; A-02/A-04 |
| Visual corrections, matched-time Eden comparisons | Pipeline log, 2026-10-16 | Not every shader/scene; B-03/L-05 |
| CPU/GPU performance and frame pacing changes | Pipeline log, 2026-10-15/16 | Not every area or cold-cache pacing; B-03/L-07 |
| Overlay navigation/options/ini and safe start | Pipeline log, 2026-10-16 | No dedicated full menu acceptance gate; A-02/A-03 |
| Crash-log copy and symbolized report | Pipeline log, 2026-10-16 | Interactive error box needs manual verification; A-04 |
| Deterministic first-battle dispatch repair | Pipeline log, 2026-10-15, commit `28c44eb` | Distinct from rare battle-loading crash; B-03 regression route |
| Poco Path shared-tail switch and longjmp repairs | Pipeline log, 2026-10-16 | Recorded route experiments, not a full-game guarantee; B-03 |

Source inspection in the preceding audit found raw RomFS storage at `psvrecomp/runtime/services/fs.c:375-388`,
a no-op Commit at `fs.c:568`, disk-cache code at `runtime/nvn/vulkan/device.c:222-253`,
`runtime/fnprof.c` and `recomp/sym.py`. Line numbers are audit references and may move after later edits.
Presence of source is not evidence that every intended path is used or correct.

## Fresh execution

See [execution notes](execution-2026-10-17.md): headless failure reproduced as run_id=5bca0b86c4 (FAIL),
then shim check run_id=dc8810b71b and host run_id=69f115de36; two 60-second boots run_id=8e0e7bcf37.
New-game metric run_id=18c9b702ee and backup/recovery run_id=e51fe74c5b have limited scopes;
the isolated restored-copy route has run_id=49191e3f3a with source manifests unchanged.
Those earlier records alone do not establish fresh guest writes. The later B-04 chain adds actual write run_id=f933f43273,
new-save backup/recovery run_id=4ec8dcdc29 and reload run_id=a9bef169e1, deliberate write-boundary interruption
run_id=7ea127f858 and post-restoration reload run_id=d6946b460e. The [recovery policy](../save-recovery-policy.md)
states the bounded guarantee, not atomic Commit or hardware power-loss durability. B-03 was closed on the current build's fresh gates plus explicit user confirmation.

## Historical failures and misleading records

- **Historical host failure:** run_id=648a2fa61b, 2026-10-16. Build exit 1 with undeclared
  `SDL_GetCurrentAudioDriver` at `audio.c:943`; B-01 owns reproduction. This is not evidence of a failed Vulkan run.
- **Do not use early PASS as full boot:** run_id=990a33212b reached `init_sdk` but recorded c0000005 at 0x20.
  Its 227,207-function report does not prove the old 271,027-function claim. Later E-02 is the frame-path evidence.
- Historical black-screen, total-silence and absent-name diagnoses are not active tasks to reimplement.
- The suspected causes of rare hash-table/battle crashes remain hypotheses. Do not infer map ids, streaming races
  or a filesystem-integrity bypass from them.

## Evidence rules for future tasks

Record build/version, source revision, dirty state, exact command, inputs/save copy, first-attempt outcome,
logs, artifacts and the test's actual assertions. Use the existing gate harness when it covers the criterion;
otherwise add a real bounded checker rather than attaching an unrelated run_id.
Manual visual/audio/hardware checks must be explicitly labeled and attributed.
Acceptance requires both implementation and the specified test; no self-reported worker success substitutes for it.

The [archived audit](archive/2026-10-17/status-audit-2026-10-17.md) contains the previous reconciliation.
The archive is historical, not another source of current priorities.
