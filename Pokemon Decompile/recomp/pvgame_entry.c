// Entry of pvgame.dll, compiled with the generated code: the per-module function tables (runtime/pvgame.h).
// Names, bases, build ids and PVGAME_ID come from layout_gen.h, written by `layout.py <exefs> --header` for the
// dump the code was recompiled from (run_boot.sh does it), so the host loads exactly the right binaries.
#include "layout_gen.h"
#include "pvgame.h"

#define MODULE(n) extern const uint64_t n##_fn_addrs[], n##_fn_count; extern const GuestFn n##_fn_ptrs[];
MODULE(main)
MODULE(subsdk0)
MODULE(sdk)

static const PvModuleTable mods[] = {
    {"main", PV_BASE_main, main_fn_addrs, main_fn_ptrs, &main_fn_count, PV_BUILD_main},
    {"subsdk0", PV_BASE_subsdk0, subsdk0_fn_addrs, subsdk0_fn_ptrs, &subsdk0_fn_count, PV_BUILD_subsdk0},
    {"sdk", PV_BASE_sdk, sdk_fn_addrs, sdk_fn_ptrs, &sdk_fn_count, PV_BUILD_sdk},
};

PVGAME_EXPORT const PvGameTables *pvgame_tables(void) {
    static const PvGameTables t = {PVGAME_ABI, PVGAME_ID, sizeof mods / sizeof mods[0], mods};
    return &t;
}
