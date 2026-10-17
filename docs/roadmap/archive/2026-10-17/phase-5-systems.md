# Phase 5: Audio, input, save and time

**Audit (2026-10-17):** audio and name entry were manually confirmed by [USER] on 2026-10-16
(`../pipeline-log.md`, swkbd/audio follow-up). This supersedes the silence/default-name notes below.
5.1 is partial: the observed game path uses audout PCM, not proof of a complete audren voice mixer.
5.2 is partial: keyboard is observed, physical gamepad/remapping/gyro/vibration coverage is not established.
5.3 remains open: the inventory records Bink `.bk2`; do not assume an MP4/USM FFmpeg path.
5.4 is partial: clock support and `PVR_CLOCK_START` are recorded, but the accelerated game day/night cycle is not
simply PC wall-clock time. 5.5 has observed boot support, not an exhaustive applet/account test.
5.6 has manual evidence for character naming; Pokemon renaming still needs a specific test.
Save persistence belongs to 3.4; atomic commit remains open there.

**In Zelda:** `services/audio.c` (audren/audout → SDL3), `hle/input.c` (`nn::hid::GetNpadState*` via HLE: keyboard and
controller via SDL3, remappable), `services/time.c`, `hid_set.c`, `acc.c`, `am.c`, `movie.c` (videos with FFmpeg).

## Tasks
- [ ] 5.1 🤖 Audio: `audren:u` (Switch audio renderer) → custom mixer → SDL3. If the game uses audio middleware
  (phase 0), it runs **inside** the recompiled code; only the renderer is ours.
- [ ] 5.2 🤖 Input: HLE of `nn::hid` (Npad Pro Controller/Handheld), keyboard + Xbox/PS controller via SDL3; configurable mapping
  Gyroscope/vibration: stub.
- [ ] 5.3 🤖 Videos (if there are `.mp4`/`.usm` in romfs): FFmpeg as in LAS.
- [ ] 5.4 🤖 Time/clock (`time:u/a/s`): validate the provided clock services, persistence and the game-owned day/night progression (not a 1:1 PC clock).
- [ ] 5.5 🤖 Account/user (`acc:u0`): a fixed local user; `am`/applet: focus, portable/dock mode (resolution).
- [ ] 5.6 🧠 Software keyboard (`swkbd`) for naming character/Pokemon: HLE with custom text box (LAS has `hle/swkbd.c`).

## Historical observations on 10/15 (superseded by 10/16 follow-up above)
- Historical 5.2 report: keyboard/Npad HLE in `hle/input.c`; do not infer a physical-controller test from keyboard input.
- 🔴 5.1 audio: **total silence** in the window. Comes after performance.
- 🔴 5.6 swkbd: without keyboard the game proceeds with a default name (`?瑱?` on the registration card).

## Exit criteria
Music and effects on the title screen; navigable menu with controls; naming character works; save persists between executions.
