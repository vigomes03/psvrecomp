# Phase 4: Graphics (NVN → Vulkan)

**Goal:** a correct first frame and then the whole game rendering in Vulkan on the RTX 3070 Ti.
It is the biggest phase: in LAS it is ~14,500 lines (`runtime/nvn/`).

**In Zelda:** every NVN function (495) intercepted by name via `nvnBootstrapLoader`/`nvnDeviceGetProcAddress`;
command buffers recorded in the game's memory (`cmdbuf.c`); objects (`objects.c`); textures and formats (`formats.c`,
`astc.c`, `texpatch.c`); **Maxwell SASS → MSL/GLSL shader translator** (`maxwell/translate.c`, ~2,100 lines) +
shaderc; Vulkan backend (`vulkan/exec.c`, `device.c`, `textures.c`, `shaders.c`); output scaling/SMAA/FSR1.

## Tasks
- [ ] 4.1 🧠 Compare Pokémon's list of NVN functions (phase 0) with LAS's 495 → list of what is missing.
- [ ] 4.2 🤖 One card per simple missing NVN function (getters/setters/state), with a command recording test.
- [ ] 4.3 🧠 Features Zelda does not use and Pokémon may use: compute shaders, tessellation/geometry,
  queries, indirect draw, more texture formats (BC1-7, assorted ASTC), MSAA. Each one becomes a subphase.
- [ ] 4.4 🧠 Shader translator: run **every** game shader through the offline translator (dump the shaders on the
  first pass) → list of unsupported SASS instructions → 🤖 cards per instruction, acceptance = fuzz
  (`test_translate`) + SPIR-V validation (shaderc + SPIRV-Tools). Reference: `eden/src/shader_recompiler`.
- [ ] 4.5 🧠 On-disk **pipeline cache** (an open world has thousands of combinations).
- [ ] 4.6 🤖 Diagnostic tools: `PVR_DEBUG_FRAME` (draw list per frame), `passes.py`, RenderDoc capture.
- [ ] 4.7 🧠 VRAM: 8 GB. Measure usage; texture streaming; free orphaned resources.

## Status on 10/15 (audited by Claude)
- 🟡 LAS's Vulkan backend ported (`nvn/vulkan`, `nvn/maxwell`, `astc`, `texpatch`, `output_scale`, SMAA, SDL3) and
  wired into `build_host.sh <dir> vulkan`; the headless (null) build still passes (gate host v400 run_id=d4b249f9a9).
- 🟡 Windowed run: `recomp/run_window.cmd` (puts `D:\msys64\ucrt64\bin` on PATH: SDL3, shaderc, libstdc++).
  20 s run in `lab/host-vk/window.log`: no FATAL, 18 to 27 fps, ~10-13 thousand draws per 2 s and **almost half
  discarded** (`skipped`), the game gets to ask for the player's name (headless swkbd). **Screen still black.** There is no
  gate for window mode yet: this is a log observation, not a milestone.
- 🟡 4.1 done in practice: with `PVR_NVN_MISSING=1`, the game asks for **18** NVN functions we do not have
  (`lab/host-v400/nvnmiss.log`): 6 `Bind*Deferred`, `OverrideSubtileSize`, `ProgramGetSubtileSize`,
  `TextureBuilderGetViewOffset`, `SetZCullZF32CompressionEnable`, and 8 checkpoint/debugging functions.
- ❌ Discarded (FALSE): everything qwen's turns produced after that (stubs outside the build with invented
  types, "nvnCommandBufferPresent", 33 batch-generated cards with repeated numbering, a false announcement of the end of
  phases 4 and 5, C# and C files written into the Hospital repository). Archived in `lab/arquivo/fallback-qwen-20261015/`,
  claims recorded as false on the scoreboard (`gates.py score`).

- 🟡 **First pixels (10/15, 02:00):** the black screen was W11's `widescreen_present_crop` stub (1x1 px viewport).
  Fixed in `pv_zelda_stubs.c`; with `LARECOMP_SCREENSHOT_EVERY=150 LARECOMP_SCREENSHOT_FROM=150` real frames come out in
  `lab/host-vk/build/frames/`: language selection (frame 150), avatar choice (450), Uva Academy crest (900).
  Text is missing in some boxes (discarded draws). Still no `window` gate: this is not the formal M3.

- 🟡 **Discards −98% (10/15):** a per-reason counter in `exec.c` (`skip why:` in the `[vk]` line) showed 98% `no_program`:
  the game does `BindProgram(NULL, FRAGMENT)` for depth-only passes and LAS kept a single program pointer.
  Now the bind is per stage (`bind_program_stages`) and a program without an FS becomes a depth-only draw (empty FS, no
  color writes). From ~13,200 to ~220 discards per 2 s, executed draws 13 thousand → 26 thousand; host v400 run_id=87b55bc362.
  ~165 remain from shaders with an unknown Maxwell instruction (4.4) and ~55 from compute.

- 🟡 **Translator (10/15):** TLD4S (W13), VMNMX (W14), VOTE (W15), global ATOM (W16) by qwen, reviewed; LEA.LO and the
  compute blob header (`0x12345679`, code at +0x100) by Claude. Compute 100% translated (dispatches 0 → every
  frame). `PVR_DIAG_UNKNOWN=1` lists every unknown instruction; `tools/verify/frame_stats.py` measures frames without opening them.
- 🔴 **Probable cause of the black 3D scene:** the only failing draws are 2 full-screen passes at 480x270 (¼ of 1080p) with
  `SUST`/`SURED` = the auto-exposure histogram. Without a histogram, exposure 0: black 3D, 2D UI ok. Disabling the depth
  test changes nothing (cutscene average 1.7 in both runs). Support for **storage images** is missing entirely:
  translator (`imageStore`/`imageAtomic*`) and backend (`STORAGE_IMAGE` descriptors, `st.img` → texture via the pool).

- 🟢 **Storage images (10/15):** infra by Claude + W17 SUST/SURED (qwen). 0 unknown instructions, 0 discarded draws.
  The 3D started to show up (character geometry in an opaque, enlarged frame, checked by [USER]).
- 🔴 **Cause of the missing text (and suspect for the 3D):** the text VS reads the glyphs via `LDG` from `cb0[17]` + 64*instance,
  but the shaders' global memory window (`gmem`, heap import) only covers `HEAP_BASE..+0xd0000000`. Pokémon puts
  **all** 1004 GPU memory pools in the alias region (SDK 13 VAMM): `0x7441c8f000..0x771116d000`, 828 MB in 2 groups
  (~130 MB at 0x7441c-0x7449x, ~800 MB at 0x76c9c-0x76fb3). Reads outside the window return 0: zero-size glyphs.
  Fix: several memory windows (one per pool group, one host import per window, base/size table in a uniform)
  and the translator picking the window by address in LDG/STG/ATOM.

- 🟢 **Review with [USER] (10/15):** M3/M4 reached in the manual test (from the logo to the start of the story, score 95/100).
  Fixed and logged in `docs/pipeline-log.md`: diagonal stripes (stencil), neon hair (BRA with flow test /
  `.CC`), player photo on the card (copy write-back). Remaining: skybox with lines, lighting artifacts, objects not
  rendered, `window` gate. The old "Next steps" of this page (black screen, 18 missing NVN functions) were superseded;
  the current order is in the [README](README.md#status-and-next-steps-review-with-user-10162026).

## Exit criterion (M3 → M4)
M3: automatic screenshot at frame N shows the logo. M4: correct title screen compared with Eden (small visual
difference measured by script).

## Risks
- Volume of shaders and variants: compiling on the fly = stutters. Mitigate with a cache and precompilation.
- Precision/blend order differences between Maxwell and Vulkan on the PC: artifacts (LAS still has lighting bugs).
