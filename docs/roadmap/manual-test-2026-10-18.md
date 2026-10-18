# Manual gameplay feedback — 2026-10-18

## Reported observation

The user tested the manually launched v4.0.0 session and explicitly reported no observed problems, visual
failures or crashes. The user also perceived performance as better than the official version. That comparison
is a subjective user observation, not a controlled cross-platform/version benchmark.

This is actual human visual feedback for the tested session, not an approval inferred from image metrics or OCR.

## Bound session and local checks

- Host build: run_id=240fe07924; preceding automated regression: run_id=74fcd35f8b.
- Manual session: lab/manual-tests/B03-20261018-034547-32373d/.
- Seed: isolated copy of the pre-battle save; keyboard/gamepad only, no scripted input, monitor 2, real audio.
- Session exit code 0; no logged FATAL/host-exception marker. The original source-save manifest is unchanged.
- Raw user statement and reduced checks: human-feedback.json beside manual-session.json and window.log.

## Acceptance boundary

The user subsequently explicitly confirmed finishing the first battle and walking freely around the map,
without observed lag, visual bugs or performance drops. First-battle completion and return to free character
control are therefore human-confirmed checkpoints, no longer dependent on OCR interpretation.

The specifically named Poco Path transition was not stated and is not inferred from generic map walking.
B-03 was subsequently closed by the fresh current-build gates (new game, 600-second copied save) plus this
manual confirmation; this report remains the human-checkpoint record and does not erase the earlier failing
run_id=e5b2041956 or establish the cause of its access violation.
