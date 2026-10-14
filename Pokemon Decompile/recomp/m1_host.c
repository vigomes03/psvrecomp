// M1 check host (verification only, not the real runtime): provides the 7 runtime symbols the generated code needs
// as traps, loads pvgame.dll and checks its tables: ABI, module count, sorted unique addresses inside each module's
// range, non-null function pointers. Exits 0 when all checks pass.
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#include "pvgame.h"

__declspec(dllexport) volatile int g_fnprof;
__declspec(dllexport) void fnprof_hit(uint64_t a, uint64_t lr, uint64_t x0) { (void)a; (void)lr; (void)x0; }
__declspec(dllexport) void rt_dispatch(Cpu *c) { fprintf(stderr, "rt_dispatch %llx: no runtime yet\n", (unsigned long long)c->pc); exit(3); }
__declspec(dllexport) void rt_svc(Cpu *c, uint32_t imm, uint64_t pc) { (void)c; fprintf(stderr, "svc %x at %llx\n", imm, (unsigned long long)pc); exit(3); }
__declspec(dllexport) void rt_brk(Cpu *c, uint32_t imm, uint64_t pc) { (void)c; fprintf(stderr, "brk %x at %llx\n", imm, (unsigned long long)pc); exit(3); }
__declspec(dllexport) void rt_udf(Cpu *c, uint64_t pc) { (void)c; fprintf(stderr, "udf at %llx\n", (unsigned long long)pc); exit(3); }
__declspec(dllexport) uint64_t rt_ticks(void) { return 0; }

int main(int argc, char **argv) {
    const char *dll = argc > 1 ? argv[1] : PVGAME_NAME;
    HMODULE h = LoadLibraryA(dll);
    if (!h) { printf("LoadLibrary(%s) failed: %lu\n", dll, GetLastError()); return 1; }
    PvGameEntry entry = (PvGameEntry)(void *)GetProcAddress(h, PVGAME_ENTRY);
    if (!entry) { printf("no %s export\n", PVGAME_ENTRY); return 1; }
    const PvGameTables *t = entry();
    int bad = t->abi != PVGAME_ABI;
    uint64_t total = 0;
    printf("pvgame: abi %u id %s, %u modules\n", t->abi, t->id, t->nmods);
    for (uint32_t m = 0; m < t->nmods; m++) {
        const PvModuleTable *mt = &t->mods[m];
        uint64_t n = *mt->count, unsorted = 0, outside = 0, nulls = 0;
        uint64_t hi = m + 1 < t->nmods ? t->mods[m + 1].base : mt->base + 0x10000000ull;
        for (uint64_t i = 0; i < n; i++) {
            if (i && mt->addrs[i] <= mt->addrs[i - 1]) unsorted++;
            if (mt->addrs[i] < mt->base || mt->addrs[i] >= hi) outside++;
            if (!mt->fns[i]) nulls++;
        }
        printf("  %-8s base %llx: %llu functions [%llx..%llx] unsorted=%llu outside=%llu null=%llu\n", mt->name,
               (unsigned long long)mt->base, (unsigned long long)n, (unsigned long long)mt->addrs[0],
               (unsigned long long)mt->addrs[n - 1], (unsigned long long)unsorted, (unsigned long long)outside,
               (unsigned long long)nulls);
        bad |= unsorted || outside || nulls || !n;
        total += n;
    }
    printf("%llu functions total: %s\n", (unsigned long long)total, bad ? "FAIL" : "OK");
    return bad;
}
