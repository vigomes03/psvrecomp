#!/usr/bin/env bash

# W12 — Implement a minimal, working PVR NVN backend for Pokémon Violet.

## Context 

The Pokémon Violet game's runtime is not yet ready to draw windowed graphics. We're building on top of the
vulkan/ directory from LAS Recomp — which has all the code needed to render to a window and show an OpenGL or
Vulkan output.

Key components:
- `device.c` creates a Vulkan context, sets up the swapchain and command buffers.
- `exec.c` is the main dispatch loop calling the draw functions: `glDrawArrays`, etc. 
- There are also texture and shader management systems that need hookups.

The runtime already has `nvn_boot.c` patching to instrument missing function calls. We now:
1. Run a headless test with `PVR_NVN_MISSING=1` (to record what's missing)
2. Implement all missing NVN functions 
3. Patch `hle/nvn_boot.c` to make the runtime call proper, rather than only logging

This phase ends after Phase 4.1 and before any card of Phase 4.2.

## Acceptance

The following commands must complete successfully:
```
cd Pokemon\ Decompile/runtime
PVR_NVN_MISSING=1 python ../../../tools/verify/gates.py run host --version v400 | head -3

# After W12, run the new backend:
cd Pokemon\ Decompile/recomp 
bash build_host.sh /d/Dev/REA/lab/host-pvr-vk vulkan
```

If everything is working correctly, you should get:
- No "missing NVN functions" in the log file (only a few non-critical logging calls)
- No "undefined symbol" errors when linking
- No "fatal" or "error" lines when running `./pvhost.exe` 
- The renderer window opens and shows frames