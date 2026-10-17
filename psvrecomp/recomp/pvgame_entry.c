// Entry of pvgame.dll, compiled with the generated code: the per-module function tables (runtime/pvgame.h).
// Names, bases, build ids and PVGAME_ID come from layout_gen.h, written by `layout.py <exefs> --header` for the
// dump the code was recompiled from (run_boot.sh does it), so the host loads exactly the right binaries.
#include "layout_gen.h"
#include "pvgame.h"

#include <fenv.h>
#include <immintrin.h>

// (PVRecomp) Fast fegetround/fesetround for the generated code (they replace libmingwex's inside pvgame.dll).
// The FP helpers (runtime/simd.h, simd_fp.h) take a slow path for every scalar FP op while FPCR.FZ or a rounding
// mode is set, and save/set/restore the host rounding mode around it. mingw's fesetround (__mingw_setfp) rewrites
// both the x87 control word and MXCSR on every call: Violet's worker threads run with FZ, and 3 threads spent ~73%
// of their samples there (cpuprof, battle, 15/10). The generated code and the helpers use SSE only (no long double),
// so the rounding mode lives in MXCSR.RC; write it only when it actually changes (nearest -> nearest is a no-op).
// (mingw's FE_* are MSVC _RC_* values, not MXCSR bits: map them explicitly.)
static int pv_rc_of(int mode) {  // FE_* -> MXCSR.RC (Intel SDM: 00 nearest, 01 down, 10 up, 11 toward zero)
    return mode == FE_TONEAREST ? 0 : mode == FE_DOWNWARD ? 1 : mode == FE_UPWARD ? 2 : mode == FE_TOWARDZERO ? 3 : -1;
}
int fegetround(void) {
    static const int fe[4] = {FE_TONEAREST, FE_DOWNWARD, FE_UPWARD, FE_TOWARDZERO};
    return fe[(_mm_getcsr() >> 13) & 3];
}
int fesetround(int mode) {
    int rc = pv_rc_of(mode);
    if (rc < 0) return 1;
    unsigned cs = _mm_getcsr(), n = (cs & ~0x6000u) | ((unsigned)rc << 13);
    if (n != cs) _mm_setcsr(n);
    return 0;
}

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
