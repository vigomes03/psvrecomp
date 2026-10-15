// PVRecomp: no randomizer. Neutral versions of the LAS Recomp hooks services/fs.c calls (no seed, no overrides).
#pragma once
#include <stdbool.h>
#include <stddef.h>
static inline const char *rando_seed_dir(void) { return NULL; }
static inline bool rando_romfs_override(const char *path, char *host, size_t size) { (void)path; (void)host; (void)size; return false; }
