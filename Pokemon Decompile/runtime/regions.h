// Guest memory map as an interval map (card W08: implementation in regions.c). Sorted, non-overlapping regions;
// setting a range overwrites whatever it overlaps (splitting partial overlaps), clearing a range carves it out, and
// adjacent regions with the same type+perm merge. PVRecomp: the LAS list keyed regions by exact start address, so the
// SDK 13 VAMM's overlapping MapPhysicalMemory / partial UnmapPhysicalMemory grew it to "FATAL: too many regions".
#pragma once
#include <stdint.h>

typedef struct { uint64_t addr, size; uint32_t type, perm; } Region;

#define REGIONS_MAX 8192

void regions_reset(void);                                                    // empty map
int regions_set(uint64_t addr, uint64_t size, uint32_t type, uint32_t perm);  // 0 ok, -1 full (map unchanged)
void regions_clear(uint64_t addr, uint64_t size);                            // carve [addr, addr+size) out
int regions_count(void);
const Region *regions_at(int i);                                             // i-th region, ascending addr
const Region *regions_find(uint64_t addr);                                   // region containing addr, or NULL
