# A — Finish the application

**State:** overlay/ini/safe-start code and recorded observations exist; fresh acceptance is open.
Depends on relevant [baseline](baseline.md) build and gameplay tasks. These tasks finish and validate the app,
not reimplement sound/rendering already observed. Keep the target at 30 fps.

## A-01 — Launcher

- [ ] Provide Play, Settings and Quit, holding game initialization until Play; select/validate local inputs and
  show actionable errors before launching a compatible build.

Split dump selection/provenance from optional generation/compilation progress UI. Never bundle or fetch game content.
**Acceptance:** launch with valid inputs; reject missing/mismatched inputs; Quit without initializing the game;
settings survive restart. Setup/generation progress has its own real test before being claimed.
**Old scope:** 8.1. Launcher remains an app deliverable, not a prerequisite to an instrumented map experiment.

## A-02 — Menu, input and safe start

- [ ] Validate existing navigation, input capture, save/reload and crash-recovery behavior using a documented matrix.

Cover keyboard, physical controller when available, focus changes, monitor/fullscreen and opening/closing the menu.
Record a missing controller test as blocked, not a keyboard substitute. Preserve the player's ini; use test copies.
**Acceptance:** menu does not leak game input; options persist; safe-start sentinel/recovery behaves as specified;
controller result is explicit. Any discovered implementation gap becomes a separate fix card.
**Old scope:** 5.2, 8.2; account/focus subtasks overlap 5.5 but do not close every applet service.

## A-03 — Video options

- [ ] Exercise internal resolution, FSR1, SMAA, VSync, monitor and fullscreen settings on a bounded combination matrix.

Compare matched scenes, frame pacing and GPU/resource behavior. Include restart after saved settings.
**Acceptance:** matrix names tested combinations and unsupported combinations; visual/manual and numeric outcomes
are separate. An exposed widget is not a feature test. No 60 fps or ultrawide expansion in this slice.
**Old scope:** 8.5 and the settings-related part of 4.7; full graphics corpus belongs to L-05.

## A-04 — Player-facing systems and error reporting

- [ ] Recheck audible music/effects, character naming, Pokemon renaming, save reload, focus behavior and an
  interactive error report with the exact preserved log path.

Tests must use copied saves. Automated crash injection is allowed only after checking the existing hook;
manual confirmation is needed for the foreground box, display placement and audible output.
**Acceptance:** named test cases, actual logs, explicit user observations for sound/name/UI, known limitations listed.
Do not require a full audren voice mixer if the selected gameplay path uses audout PCM; investigate actual gaps.
**Old scope:** 5.1/5.2/5.6, focus part of 5.5 and phase 7 crash-notice follow-up. Broader systems remain L-06.

## Exit

A-01 through A-04 define the app slice. M7 is not declared from overlay presence alone.
Optional app extensions are retained in the [backlog](backlog.md), not silently abandoned.
