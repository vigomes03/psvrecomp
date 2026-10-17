#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// Cluster GPU memory pools into imported windows (exec.c gwin_refresh). W18: qwen3-coder-64k t1 + loop fixed by Claude.
typedef struct { uint64_t base, size; } GwinRange;

static int range_compare(const void *a, const void *b) {
    const GwinRange *ra = (const GwinRange *)a;
    const GwinRange *rb = (const GwinRange *)b;
    if (ra->base < rb->base) return -1;
    if (ra->base > rb->base) return 1;
    return 0;
}

static uint64_t align_down(uint64_t value, uint64_t align) {
    return value & ~(align - 1);
}

static uint64_t align_up(uint64_t value, uint64_t align) {
    return (value + align - 1) & ~(align - 1);
}

int gwin_cluster(const GwinRange *pools, int n, uint64_t align, uint64_t gap, uint64_t maxspan,
                 GwinRange *out, int maxout) {
    if (n == 0) {
        return 0;
    }
    
    if (maxout <= 0) {
        return -1;
    }
    
    // Copiar e alinhar pools
    GwinRange *aligned_pools = malloc(n * sizeof(GwinRange));
    if (!aligned_pools) {
        return -1;
    }
    
    for (int i = 0; i < n; i++) {
        aligned_pools[i].base = align_down(pools[i].base, align);
        aligned_pools[i].size = align_up(pools[i].base + pools[i].size, align) - aligned_pools[i].base;
    }
    
    // Ordenar por base
    qsort(aligned_pools, n, sizeof(GwinRange), range_compare);
    
    // (Claude: t1 ignored `gap` and emitted the over-maxspan window; rewritten)
    int out_count = 0;
    GwinRange cur = aligned_pools[0];
    for (int i = 1; i < n; i++) {
        uint64_t cur_end = cur.base + cur.size;
        uint64_t p_end = aligned_pools[i].base + aligned_pools[i].size;
        uint64_t new_end = p_end > cur_end ? p_end : cur_end;
        uint64_t dist = aligned_pools[i].base > cur_end ? aligned_pools[i].base - cur_end : 0;
        if (dist <= gap && new_end - cur.base <= maxspan) {
            cur.size = new_end - cur.base;
            continue;
        }
        if (out_count >= maxout) {
            free(aligned_pools);
            return -1;
        }
        out[out_count++] = cur;
        cur = aligned_pools[i];
    }
    
    // Save the last window
    if (out_count >= maxout) {
        free(aligned_pools);
        return -1;
    }
    out[out_count++] = cur;
    
    free(aligned_pools);
    return out_count;
}
