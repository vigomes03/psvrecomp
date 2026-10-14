// Game code library interface (pvgame.dll): the recompiled modules' function tables, found by name when the host
// loads the library. Generalizes LAS Recomp's gamelib.h (main + sdk) to N modules (Pokémon: main, subsdk0, sdk).
// Module bases come from recomp/layout.py.
#pragma once
#include <stdint.h>

#include "cpu.h"

#if defined(_WIN32)
#define PVGAME_NAME "pvgame.dll"
#define PVGAME_EXPORT __declspec(dllexport)
#else
#define PVGAME_NAME "pvgame.so"
#define PVGAME_EXPORT __attribute__((visibility("default")))
#endif

#ifndef PVGAME_ID
#define PVGAME_ID "dev"
#endif
#define PVGAME_ABI 1

typedef struct {
    const char *name;        // "main", "subsdk0", "sdk"
    uint64_t base;           // guest load address (layout.py)
    const uint64_t *addrs;   // sorted guest addresses of the recompiled functions
    const GuestFn *fns;      // the functions at them
    const uint64_t *count;
} PvModuleTable;

typedef struct {
    uint32_t abi;            // PVGAME_ABI
    const char *id;          // PVGAME_ID: what the library was built from
    uint32_t nmods;
    const PvModuleTable *mods;
} PvGameTables;

typedef const PvGameTables *(*PvGameEntry)(void);
#define PVGAME_ENTRY "pvgame_tables"
