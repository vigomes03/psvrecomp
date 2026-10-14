// Entry of pvgame.dll, compiled with the generated code: the per-module function tables (runtime/pvgame.h).
// Bases must match recomp/layout.py (checked by the host against the loaded NSOs later).
#include "pvgame.h"

#define MODULE(n) extern const uint64_t n##_fn_addrs[], n##_fn_count; extern const GuestFn n##_fn_ptrs[];
MODULE(main)
MODULE(subsdk0)
MODULE(sdk)

static const PvModuleTable mods[] = {
    {"main", 0x7000000000ull, main_fn_addrs, main_fn_ptrs, &main_fn_count},
    {"subsdk0", 0x7004400000ull, subsdk0_fn_addrs, subsdk0_fn_ptrs, &subsdk0_fn_count},
    {"sdk", 0x7004c00000ull, sdk_fn_addrs, sdk_fn_ptrs, &sdk_fn_count},
};

PVGAME_EXPORT const PvGameTables *pvgame_tables(void) {
    static const PvGameTables t = {PVGAME_ABI, PVGAME_ID, sizeof mods / sizeof mods[0], mods};
    return &t;
}
