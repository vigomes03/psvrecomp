// PVRecomp debug: log nn::diag aborts / asserts with their strings, then run the real SDK code (which ends in
// svcBreak). Release builds of the game strip the diag log observer, so without this an abort shows only the
// backtrace. Always on (an abort is fatal anyway, the cost is a few overrides).
#include <stdio.h>

#include "hle.h"

#define GSTR(a) ((a) >= GUEST_LO && (a) < GUEST_HI ? (const char *)(uintptr_t)(a) : "(null)")

typedef struct { const char *sym; GuestFn orig; uint64_t addr; } Hooked;
static Hooked hooks[] = {
    {"_ZN2nn4diag6detail9AbortImplEPKcS3_S3_iS3_z", NULL, 0},  // (condition, function, file, line, fmt, ...)
    {"_ZN2nn4diag6detail9AbortImplEPKcS3_S3_i", NULL, 0},      // (condition, function, file, line)
    {"_ZN2nn4diag6detail9AbortImplEPKcS3_S3_iPKNS_6ResultES3_z", NULL, 0},  // (..., line, result, fmt, ...)
};

static void log_abort(Cpu *c, int which) {
    LOG("[diag] ABORT %s: condition \"%s\" in %s (%s:%llu)\n", hooks[which].sym, GSTR(c->x[0]), GSTR(c->x[1]),
        GSTR(c->x[2]), (unsigned long long)(uint32_t)c->x[3]);
    if (which == 0) {
        LOG("[diag]   message fmt \"%s\" args %llx %llx %llx\n", GSTR(c->x[4]), (unsigned long long)c->x[5],
            (unsigned long long)c->x[6], (unsigned long long)c->x[7]);
        for (int i = 5; i < 8; i++)  // %s arguments: show the strings (e.g. the Lua error message on the heap)
            if (c->x[i] >= GUEST_LO && c->x[i] < GUEST_HI) LOG("[diag]   arg x%d = \"%.400s\"\n", i, GSTR(c->x[i]));
    }
    if (which == 2) {
        uint64_t r = c->x[4];
        LOG("[diag]   result %#x, fmt \"%s\"\n", r >= GUEST_LO && r < GUEST_HI ? *(uint32_t *)(uintptr_t)r : 0,
            GSTR(c->x[5]));
    }
    LOG("[diag]   called from lr %llx\n", (unsigned long long)c->x[30]);
}

#define HOOK(i) static void hook_##i(Cpu *c) { log_abort(c, i); hooks[i].orig(c); }
HOOK(0)
HOOK(1)
HOOK(2)
static HostFn hook_fns[] = {hook_0, hook_1, hook_2};

void diag_install(void) {
    for (unsigned i = 0; i < sizeof hooks / sizeof hooks[0]; i++) {
        uint64_t a = loader_find_symbol(hooks[i].sym);
        GuestFn f = a ? dispatch_lookup(a) : NULL;
        if (!f) continue;
        hooks[i].addr = a;
        hooks[i].orig = f;
        hle_override(a, hook_fns[i], hooks[i].sym);
    }
}
