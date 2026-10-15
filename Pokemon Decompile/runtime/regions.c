#include <stdint.h>
#include <string.h>
#include "regions.h"

static Region g_regions[REGIONS_MAX];
static int g_n;

void regions_reset(void) {
    g_n = 0;
}

static int find_region(uint64_t addr) {
    int left = 0, right = g_n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (g_regions[mid].addr <= addr && addr < g_regions[mid].addr + g_regions[mid].size)
            return mid;
        else if (g_regions[mid].addr > addr)
            right = mid - 1;
        else
            left = mid + 1;
    }
    return -1;
}

static int find_insert_pos(uint64_t addr) {
    int left = 0, right = g_n;
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (g_regions[mid].addr < addr)
            left = mid + 1;
        else
            right = mid;
    }
    return left;
}

static void merge_left(int *i) {
    int pos = *i;
    if (pos > 0 && g_regions[pos-1].addr + g_regions[pos-1].size == g_regions[pos].addr &&
        g_regions[pos-1].type == g_regions[pos].type && g_regions[pos-1].perm == g_regions[pos].perm) {
        g_regions[pos-1].size += g_regions[pos].size;
        memmove(&g_regions[pos], &g_regions[pos+1], (g_n - pos - 1) * sizeof(Region));
        g_n--;
        *i = pos - 1;
    }
}

static void merge_right(int i) {
    if (i + 1 < g_n && g_regions[i].addr + g_regions[i].size == g_regions[i+1].addr &&
        g_regions[i].type == g_regions[i+1].type && g_regions[i].perm == g_regions[i+1].perm) {
        g_regions[i].size += g_regions[i+1].size;
        memmove(&g_regions[i+1], &g_regions[i+2], (g_n - i - 2) * sizeof(Region));
        g_n--;
    }
}

static int clear_impl(uint64_t addr, uint64_t size) {
    if (size == 0)
        return 0;
    
    uint64_t end = addr + size;
    int i = find_insert_pos(addr);
    if (i > 0 && g_regions[i-1].addr + g_regions[i-1].size > addr) 
        i--;
    
    while (i < g_n && g_regions[i].addr < end) {
        uint64_t r_start = g_regions[i].addr;
        uint64_t r_end = g_regions[i].addr + g_regions[i].size;
        
        if (r_start >= addr && r_end <= end) {
            // fully covered
            memmove(&g_regions[i], &g_regions[i+1], (g_n - i - 1) * sizeof(Region));
            g_n--;
        } else if (r_start < addr && r_end > end) {
            // strictly inside
            uint64_t left_size = addr - r_start;
            uint64_t right_size = r_end - end;
            
            if (g_n == REGIONS_MAX)
                return -1;  // don't split, keep only the left part
            
            memmove(&g_regions[i+1], &g_regions[i], (g_n - i) * sizeof(Region));
            g_regions[i].size = left_size;
            g_regions[i+1].addr = end;
            g_regions[i+1].size = right_size;
            g_n++;
            break;  // no more overlaps
        } else if (r_start < addr && r_end > addr) {
            // covers only its right part
            g_regions[i].size = addr - r_start;
            i++;
        } else if (r_start >= addr && r_start < end) {
            // covers only its left part
            g_regions[i].addr = end;
            g_regions[i].size = r_end - end;
            i++;
        } else {
            i++;
        }
    }
    return 0;
}

void regions_clear(uint64_t addr, uint64_t size) {
    clear_impl(addr, size);
}

int regions_set(uint64_t addr, uint64_t size, uint32_t type, uint32_t perm) {
    if (size == 0)
        return 0;

    // Simple snapshot-try-roll-back approach
    static Region backup[REGIONS_MAX];
    int bn = g_n;
    memcpy(backup, g_regions, g_n * sizeof(Region));
    
    if (g_n + 2 > REGIONS_MAX) {
        // Check if we can do it without overflow by simulating the operation
        int old_n = g_n;
        int overlaps = 0;
        
        for (int i = find_insert_pos(addr); i < g_n && g_regions[i].addr < addr + size; i++) {
            uint64_t r_start = g_regions[i].addr;
            uint64_t r_end = g_regions[i].addr + g_regions[i].size;
            
            if (r_start >= addr && r_end <= addr + size)
                overlaps++;
            else
                overlaps += 2; // partial overlap, might split
        }
        
        int new_n = old_n - overlaps + 1;
        if (new_n > REGIONS_MAX) {
            memcpy(g_regions, backup, bn * sizeof(Region));
            g_n = bn;
            return -1;
        }
    }

    regions_clear(addr, size);
    
    int pos = find_insert_pos(addr);
    
    memmove(&g_regions[pos+1], &g_regions[pos], (g_n - pos) * sizeof(Region));
    g_regions[pos].addr = addr;
    g_regions[pos].size = size;
    g_regions[pos].type = type;
    g_regions[pos].perm = perm;
    g_n++;
    
    int new_pos = pos;
    merge_left(&new_pos);
    merge_right(new_pos);
    
    return 0;
}

int regions_count(void) {
    return g_n;
}

const Region *regions_at(int i) {
    if (i < 0 || i >= g_n)
        return NULL;
    return &g_regions[i];
}

const Region *regions_find(uint64_t addr) {
    int i = find_region(addr);
    if (i == -1)
        return NULL;
    return &g_regions[i];
}
