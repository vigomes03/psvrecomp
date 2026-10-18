# B-03 route comparison

## Evidence boundaries

This compares recorded metric checks, not equivalent controlled experiments or human visual approval.
Gate duration includes capture/stat processing; it is not the requested gameplay duration. All runs below have
passing recorded window checks, but refer to their own artifacts/source state. Later source changes are not
retroactively certified by these records.

| Role | Run id | Requested gameplay | Presented frames | Rendered captures | Scene changes | Final FPS windows |
|---|---|---|---|---|---|---|
| Historical E-06, new game | run_id=312d34de1a | 60 s | 1,660 | 7/11 | 10 | 28.7 / 28.4 |
| New-game comparison | run_id=18c9b702ee | 60 s | 1,641 | 7/11 | 10 | 28.7 / 28.3 |
| Historical E-07, copied save | run_id=c6a80b10d8 | 600 s | 17,227 | 111/114 | 32 | 28.9 / 28.9 |
| Copied-save comparison | run_id=64b1817ee3 | 600 s | 17,167 | 111/114 | 29 | 28.9 / 28.9 |
| Isolated restored-copy comparison | run_id=49191e3f3a | 600 s | 17,168 | 111/114 | 29 | 28.8 / 28.8 |
| Current build, new game (B-03 closure) | run_id=38c0cfbc90 | 60 s | 1,643 | 7/11 | 10 | 28.8 / 28.4 |
| Current build, copied save (B-03 closure) | run_id=e559998a17 | 600 s | 17,100 | 111/114 | 25 | 28.4 / 29.2 |

Each recorded first attempt reported no FATAL/host access violation. The measured frame, rendering and final-FPS
checks stayed above their gate thresholds. Different frame/scene-change counts do not by themselves identify a
regression or establish that the exact same semantic route was followed; input, source changes, loading and timing
must be considered before attributing a cause.

## Semantic coverage

- New-game and copied-save metric routes have records; explicit name entry, character control and exact location
  transitions are not established by image metrics alone.
- First-battle and Poco Path regressions need individually identified checkpoints on the supported copied saves.
  Historical fixes are not a fresh execution of those transitions.
- Local OCR later identified the main menu, a tutorial modal, and the Save menu option in retained captures.
  These are narrowly named automated screen observations, not user visual approval of the full baseline route.
- Fresh save writing, deliberate write-boundary interruption, recovery and actual reload are documented separately
  in [save recovery policy](../save-recovery-policy.md), including run_id=7ea127f858 and run_id=d6946b460e.

## Fresh first-battle attempt

The 180-second copied pre-battle scenario has run_id=e5b2041956 (FAIL). Its first child recorded a host access
violation at address 0x8 and stopped at presented frame 363. The existing run_auto wrapper retried; the later
child reached 5,113 frames, 30/34 rendered captures, 26 scene changes and final windows 29.0/29.3 fps. Those
later metrics do not erase the first failure: the gate correctly remains failed.

All attempt logs and later-child frames are preserved in ignored lab/baseline-20261017/first-battle-e5b2041956/.
The original source manifest stayed unchanged. Local OCR found Run and Bag labels in a later-child frame;
that is a battle-UI candidate, not proof of the first attempt or of battle completion. No user approval is inferred.
The crash cause is unclassified. It must be surfaced as a B-03 route blocker, not silently attributed to the
previous rare-crash hypothesis or hidden by another retry. Independent read-only R work may proceed.

[The 2026-10-18 triage](crash-triage-2026-10-18.md) binds the native fault and a consistent guest caller/callee
pair to matching binaries and a hash-verified source image. A separate one-attempt 30-second diagnostic did
not reproduce the exception; that is neither a fix nor a passing B-03 route. The original gate remains FAIL.

## Post-instrumentation regression, not semantic acceptance

[W32 diagnostic/reporting work](windows-fault-context-2026-10-18.md) has a final source-bound Vulkan build
run_id=240fe07924, link run_id=af480d2048 and 60-second copied pre-battle window run_id=74fcd35f8b.
Its first attempt had no crash; the final periodic frame counter was 1,646, with 8/11 rendered captures and
final FPS windows 29.1/29.0. Source-save hashes remained unchanged. This does not repair the historical failure,
prove battle completion or substitute for outstanding B-03 semantic/user checks.

[W33 checkpoint review](../../work/cards/W33-retained-checkpoint-review.md) checked retained full-frame and
enlarged-crop OCR observations; none established a reliable battle-ending checkpoint. Subsequent explicit
[manual feedback](manual-test-2026-10-18.md) confirmed first-battle completion and free map movement without
observed lag, visual issues or performance drops. Those checkpoints are confirmed by the user, not inferred
from OCR. Named transitions and formal route coverage remain separate; independent
[R-01 scoped analysis](scoped-analysis-2026-10-18.md) does not change that boundary.

## Worker review

Qwen draft W25 supplied the three comparison rows for the newer runs; those numeric fields were checked against
actual gate checks. The call used a 4,096-token context and returned an unclosed block/truncated
last line (worker exit 2). The full draft was rejected. Its claim treating gate wall durations as route durations
and its broader input-presence claims were not adopted. The historical rows and scope limits above were added
from direct record review, not attributed to the worker.

B-03 is closed (see [baseline](baseline.md)) on the current build's fresh new-game and 600-second copied-save gates
plus explicit user confirmation. No unattended wait or silence is interpreted as approval.
