# W05 — `pl:u` shared font service (`runtime/services/pl.c`)

## Goal
Pokémon Violet polls `pl:u` `GetLoadState` in a loop until the system shared fonts are "Loaded" (boot log 14/10:
the game never gets past it). Implement the service so the fonts load from TTF files on the host and are exposed to
the game through a 17 MiB shared memory block, exactly like Horizon does.

Output: ONE C file, `pl.c`. C11, clang (MinGW UCRT64) `-Wall`. Start with:
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../ipc.h"
#include "../kernel.h"
```

## Runtime API you may use (and nothing else)
- `SERVICE("pl:u", pl_u) { ... }` defines the handler `static void pl_u(Service *s, IpcReq *req, IpcResp *resp)`
  (macro from ipc.h; use it exactly like this, once). In the body: `(void)s;`.
- `req->cmd` = command id. Input raw data: `IN(type, byte_offset)`. Output raw data: `OUT(type, byte_offset) = v;`
  then `resp_size(resp, total_bytes);` (call it with the end of the furthest field you wrote).
- `IpcBuf *out_buf(IpcReq *req, int i)` = the i-th output buffer (fields `uint64_t addr, size`; addr is a pointer
  usable directly as `(uint8_t *)(uintptr_t)b->addr`), may return NULL.
- Returning a handle: `resp->copy_handles[resp->ncopy++] = handle;`
- `KSharedMem *kernel_create_shared_memory(uint64_t size, void (*on_map)(KSharedMem *), uint32_t *handle);`
  creates the block; `on_map(s)` is called when the game maps it: `s->guest_addr` is where (copy contents there).
- `LOG(...)` = fprintf(stderr, ...).

## Font data
- 6 font types (`uint32_t type` = 0..5): 0 Japan/US/Europe standard, 1 Chinese simplified, 2 extended Chinese
  simplified, 3 Chinese traditional, 4 Korean, 5 Nintendo extended (icons).
- Directory: `getenv("PVR_SYSFONT_DIR")`, or `"sysfont"` if unset. Files: `<dir>/<type>.ttf` (`0.ttf` … `5.ttf`).
  A missing file just leaves that font with size 0 (log `[pl] font %u missing (%s)\n` once).
- Load all fonts ONCE (static flag) into a static host buffer `static uint8_t g_font_mem[0x1100000];` the first time
  any command runs. Layout, fonts in type order, starting at offset 0, each font = 8-byte header + TTF bytes:
  - `u32` at `off`     = `0x18029a7f`
  - `u32` at `off + 4` = `ttf_size ^ 0x49621806`
  - TTF bytes at `off + 8` (unchanged), then the next font starts at `off + 8 + ttf_size` rounded up to 4.
  - Region of the font: `offset = off + 8`, `size = ttf_size` (the header is not part of the region).
  - If a font does not fit in 0x1100000, skip it (size 0) and log it.
- Log once after loading: `[pl] shared fonts: %u loaded, %u bytes\n`.

## Commands (`pl:u`, CMIF)
| cmd | name | input raw | output |
|---|---|---|---|
| 0 | RequestLoad | `u32 type` @0 | nothing (`resp_size(resp, 0)` not needed) |
| 1 | GetLoadState | `u32 type` @0 | `u32` @0 = 1 (Loaded) |
| 2 | GetSize | `u32 type` @0 | `u32` @0 = region size (0 for type > 5) |
| 3 | GetSharedMemoryAddressOffset | `u32 type` @0 | `u32` @0 = region offset (0 for type > 5) |
| 4 | GetSharedMemoryNativeHandle | — | copy handle of the shared memory (create it once: size `0x1100000`, `on_map` copies all of `g_font_mem` to `s->guest_addr`) |
| 5 and 6 | GetSharedFontInOrderOfPriority(ForSystem) | `u64 language_code` @0 (ignored) | out buffers 0,1,2 = arrays of `u32`: font codes, offsets, sizes. Fill `n` = min(6, each buffer size / 4) entries with type `i`, region offset, region size. Raw out: `u8` @0 = 1 (fonts loaded), `u32` @4 = n; `resp_size(resp, 8)` |
| other | | | `LOG("[pl] cmd %u (ok)\n", req->cmd);` |

## Acceptance (checked by script)
`recomp/test_pl.c` includes your file with stubbed runtime functions, writes two tiny fake `.ttf` files (100 and 7
bytes) as types 0 and 1 in a temp dir, and checks: GetLoadState → 1; GetSize(0)=100, GetSize(1)=7, GetSize(2)=0;
offset(0)=8, offset(1)=8+100+8=116; header words at 0 and 108; TTF bytes copied; cmd 5 with three 6-entry buffers
returns n=6 and the same offsets/sizes; cmd 4 returns a copy handle and the on_map copies the block.
