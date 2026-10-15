// Acceptance test for card W03 (runtime/nvn/null_backend.c). Build + run: see work/cards/W03-nvn-null-backend.md.
// Prints "W03 PASS" and exits 0 only if every check holds; stderr of the backend goes to a file the script checks.
#include <stdint.h>
#include <stdio.h>

#include "nvn.h"

void backend_init(void);
void backend_execute(uint64_t handle);
void backend_present(NvnTexture *tex);
void backend_texture_destroyed(NvnTexture *tex);
void backend_pool_written(uint64_t addr, uint64_t size);
void renderer_sync(void);
uint64_t renderer_fence_seq(void);
void renderer_wait_seq(uint64_t seq);
void renderer_flush(void);
uint64_t nvn_null_frames(void);
uint64_t nvn_null_executes(void);

// The runtime symbols nvn.h/hle.h may reference are not needed by the backend itself.
int main(void) {
    int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FAIL %s\n", #c); fails++; } } while (0)
    backend_init();
    CHECK(renderer_fence_seq() == 1);
    CHECK(renderer_fence_seq() == 2);
    CHECK(renderer_fence_seq() == 3);
    NvnTexture t = {0};
    t.width = 1920; t.height = 1080; t.format = 37;
    for (int i = 0; i < 3; i++) backend_execute(0x1000 + i);
    for (int i = 0; i < 4; i++) backend_present(&t);
    backend_present(NULL);
    backend_texture_destroyed(&t);
    backend_pool_written(0x7000000000ull, 0x1000);
    renderer_sync();
    renderer_wait_seq(2);
    renderer_flush();
    CHECK(nvn_null_frames() == 5);
    CHECK(nvn_null_executes() == 3);
    printf(fails ? "W03 FAIL (%d)\n" : "W03 PASS\n", fails);
    return fails != 0;
}
