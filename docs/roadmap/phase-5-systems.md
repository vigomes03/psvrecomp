# Phase 5: Audio, input, save and time

**In Zelda:** `services/audio.c` (audren/audout → SDL3), `hle/input.c` (`nn::hid::GetNpadState*` via HLE: keyboard and
controller via SDL3, remappable), `services/time.c`, `hid_set.c`, `acc.c`, `am.c`, `movie.c` (videos with FFmpeg).

## Tasks
- [ ] 5.1 🤖 Audio: `audren:u` (Switch audio renderer) → custom mixer → SDL3. If the game uses audio middleware
  (phase 0), it runs **inside** the recompiled code; only the renderer is ours.
- [ ] 5.2 🤖 Input: HLE of `nn::hid` (Npad Pro Controller/Handheld), keyboard + Xbox/PS controller via SDL3; configurable mapping
  Gyroscope/vibration: stub.
- [ ] 5.3 🤖 Videos (if there are `.mp4`/`.usm` in romfs): FFmpeg as in LAS.
- [ ] 5.4 🤖 Time/clock (`time:u/a/s`): the game clock (day/night) follows the PC clock.
- [ ] 5.5 🤖 Account/user (`acc:u0`): a fixed local user; `am`/applet: focus, portable/dock mode (resolution).
- [ ] 5.6 🧠 Software keyboard (`swkbd`) for naming character/Pokemon: HLE with custom text box (LAS has `hle/swkbd.c`).

## Status as of 10/15 (review with [USER])
- 🟢 5.2 input: keyboard and controller (Npad HLE in `hle/input.c`), confirmed by [USER].
- 🔴 5.1 audio: **total silence** in the window. Comes after performance.
- 🔴 5.6 swkbd: without keyboard the game proceeds with a default name (`?瑱?` on the registration card).

## Exit criteria
Music and effects on the title screen; navigable menu with controls; naming character works; save persists between executions.
