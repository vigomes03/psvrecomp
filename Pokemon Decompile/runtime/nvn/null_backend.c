#include <stdatomic.h>
#include "nvn.h"

static _Atomic uint64_t frame_count = 0;
static _Atomic uint64_t execute_count = 0;
static _Atomic uint64_t fence_seq = 0;

void backend_init(void) {
    LOG("[nvn-null] headless backend (no rendering)\n");
}

void backend_execute(uint64_t handle) {
    (void)handle;
    atomic_fetch_add(&execute_count, 1);
}

void backend_present(NvnTexture *tex) {
    uint64_t current_frame = atomic_fetch_add(&frame_count, 1) + 1;
    
    // Check if frame number is a power of two
    if ((current_frame & (current_frame - 1)) == 0) {
        if (tex != NULL) {
            LOG("[nvn-null] present #%llu (%ux%u fmt %u, %llu command lists)\n",
                current_frame, tex->width, tex->height, tex->format, execute_count);
        } else {
            LOG("[nvn-null] present #%llu (0x0 fmt 0, %llu command lists)\n",
                current_frame, execute_count);
        }
    }
}

void backend_texture_destroyed(NvnTexture *tex) {
    (void)tex;
}

void backend_pool_written(uint64_t addr, uint64_t size) {
    (void)addr;
    (void)size;
}

void renderer_sync(void) {
    // no-op
}

uint64_t renderer_fence_seq(void) {
    return atomic_fetch_add(&fence_seq, 1) + 1;
}

void renderer_wait_seq(uint64_t seq) {
    (void)seq;
}

void renderer_flush(void) {
    // no-op
}

uint64_t nvn_null_frames(void) {
    return atomic_load(&frame_count);
}

uint64_t nvn_null_executes(void) {
    return atomic_load(&execute_count);
}
