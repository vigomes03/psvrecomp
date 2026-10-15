# W03 — null renderer backend for the headless NVN layer (`runtime/nvn/null_backend.c`)

## Goal
The PVRecomp host runs the game **headless** (no window, no GPU). The NVN object layer (`runtime/nvn/objects.c`,
`cmdbuf.c`, ported from LAS Recomp) records everything on the CPU and calls a renderer backend. Write the backend that
does **no rendering**: it only keeps fence sequence numbers coherent and counts/presents frames in the log.

Output: ONE C file, `null_backend.c`. C11, compiled with clang on Windows (MinGW UCRT64), `-I runtime`.

## Existing API you may use (and nothing else)
From `nvn.h` (given as context file): the type `NvnTexture` (fields `width`, `height`, `format` are `uint32_t`).
From `rt.h` (included by `nvn.h`): `LOG(...)` = `fprintf(stderr, ...)`.
Standard C: `<stdatomic.h>`, `<stdint.h>`, `<stdbool.h>`, `<stdio.h>`.
Start the file with `#include <stdatomic.h>` then `#include "nvn.h"`.

## Functions to implement (exact signatures, all non-static)
```c
void backend_init(void);                              // log once: "[nvn-null] headless backend (no rendering)\n"
void backend_execute(uint64_t handle);                // count executed command lists; nothing else
void backend_present(NvnTexture *tex);                // count frames; log (see below)
void backend_texture_destroyed(NvnTexture *tex);      // no-op
void backend_pool_written(uint64_t addr, uint64_t size);  // no-op
void renderer_sync(void);                             // no-op (all work is always complete)
uint64_t renderer_fence_seq(void);                    // atomically ++counter, return the NEW value (first call -> 1)
void renderer_wait_seq(uint64_t seq);                 // no-op (every sequence is already complete)
void renderer_flush(void);                            // no-op
uint64_t nvn_null_frames(void);                       // number of backend_present calls so far
uint64_t nvn_null_executes(void);                     // number of backend_execute calls so far
```
- Counters are `static _Atomic uint64_t`, updated with `atomic_fetch_add` (several guest threads call these).
- `backend_present`: after incrementing, if the new frame number N is a power of two (1, 2, 4, 8, ...), log exactly
  `"[nvn-null] present #%llu (%ux%u fmt %u, %llu command lists)\n"` with N, `tex->width`, `tex->height`,
  `tex->format`, and the current execute count. If `tex` is NULL, log the same line with 0x0 fmt 0.
- Unused parameters: cast to `(void)`.

## Acceptance (checked by a script, not by reading)
`tools/.../test_null_backend.c` links your file and checks: `renderer_fence_seq()` returns 1, 2, 3 on three calls;
after 5 `backend_present` + 3 `backend_execute` calls `nvn_null_frames()==5`, `nvn_null_executes()==3`; stderr has
present lines for #1, #2, #4 only; `backend_present(NULL)` does not crash. Compiles with `-Wall -Werror`.
