// (PVRecomp) Sampling CPU profiler. PVR_CPUPROF=<from_s>:<to_s> (seconds since start): every ~1 ms each registered
// guest thread is suspended, its host RIP read, and resumed. At <to_s> build/cpuprof.txt gets one line per
// (thread, module, rva) with the sample count; for samples outside pvgame.dll (runtime helpers, CRT, waits in ntdll)
// the guest return address (x30) is kept too, so the report can name the game function that called the helper.
// Report: tools/rea/cpuprof_report.py <cpuprof.txt> <pvgame.dll> <pvhost.exe>.
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <mmsystem.h>

#include "cpu.h"
#include "platform.h"
#include "rt.h"

#define MAXT 128
static struct { HANDLE h; DWORD tid; const Cpu *cpu; uint32_t guest_handle; uint64_t samples; } th[MAXT];
static _Atomic int nth;
static SRWLOCK th_lock = SRWLOCK_INIT;

#define NSLOT (1 << 20)
static struct { uint64_t rip, lr; uint32_t t; uint32_t count; } slot[NSLOT];
static uint64_t lost;

static double t_from = -1, t_to;

void cpuprof_register_thread(const Cpu *cpu, uint32_t guest_handle) {
    if (t_from < 0) return;
    HANDLE h;
    if (!DuplicateHandle(GetCurrentProcess(), GetCurrentThread(), GetCurrentProcess(), &h,
                         THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, 0))
        return;
    AcquireSRWLockExclusive(&th_lock);
    int i = atomic_load(&nth);
    if (i < MAXT) {
        th[i].h = h; th[i].tid = GetCurrentThreadId(); th[i].cpu = cpu; th[i].guest_handle = guest_handle;
        atomic_store(&nth, i + 1);
    } else CloseHandle(h);
    ReleaseSRWLockExclusive(&th_lock);
}

static HMODULE g_game;
static void add(uint32_t t, uint64_t rip, uint64_t lr) {
    uint64_t k = (rip * 0x9E3779B97F4A7C15ull) ^ (lr * 0xC2B2AE3D27D4EB4Full) ^ t;
    for (uint32_t i = (uint32_t)(k >> 44), n = 0; n < 64; i = (i + 1) & (NSLOT - 1), n++) {
        if (!slot[i].count) { slot[i].rip = rip; slot[i].lr = lr; slot[i].t = t; slot[i].count = 1; return; }
        if (slot[i].rip == rip && slot[i].lr == lr && slot[i].t == t) { slot[i].count++; return; }
    }
    lost++;
}

static void dump(void) {
    const char *out = getenv("PVR_CPUPROF_OUT") ? getenv("PVR_CPUPROF_OUT") : "build/cpuprof.txt";
    FILE *f = fopen(out, "w");
    if (!f) { LOG("[cpuprof] cannot write %s\n", out); return; }
    int n = atomic_load(&nth);
    for (int i = 0; i < n; i++)
        fprintf(f, "T %d tid=%lu guest=%x samples=%llu\n", i, th[i].tid, th[i].guest_handle, (unsigned long long)th[i].samples);
    char name[MAX_PATH];
    for (uint32_t i = 0; i < NSLOT; i++) {
        if (!slot[i].count) continue;
        HMODULE m = NULL;
        const char *mod = "?";
        uint64_t base = 0;
        if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                               (LPCSTR)(uintptr_t)slot[i].rip, &m) && GetModuleFileNameA(m, name, sizeof name)) {
            mod = strrchr(name, '\\') ? strrchr(name, '\\') + 1 : name;
            base = (uint64_t)(uintptr_t)m;
        }
        fprintf(f, "S %u %s %llx %llx %u\n", slot[i].t, mod, (unsigned long long)(slot[i].rip - base),
                (unsigned long long)slot[i].lr, slot[i].count);
    }
    fclose(f);
    LOG("[cpuprof] %d threads, written %s (lost %llu)\n", n, out, (unsigned long long)lost);
}

static DWORD WINAPI sampler(void *arg) {
    (void)arg;
    timeBeginPeriod(1);
    uint64_t f0 = GetTickCount64();
    while ((GetTickCount64() - f0) / 1000.0 < t_from) Sleep(50);
    g_game = GetModuleHandleA("pvgame.dll");
    LOG("[cpuprof] sampling %.0f-%.0f s (pvgame.dll %p)\n", t_from, t_to, (void *)g_game);
    while ((GetTickCount64() - f0) / 1000.0 < t_to) {
        int n = atomic_load(&nth);
        for (int i = 0; i < n; i++) {
            if (SuspendThread(th[i].h) == (DWORD)-1) continue;
            CONTEXT ctx = {.ContextFlags = CONTEXT_CONTROL};
            BOOL ok = GetThreadContext(th[i].h, &ctx);
            uint64_t lr = th[i].cpu ? th[i].cpu->x[30] : 0;
            ResumeThread(th[i].h);
            if (!ok) continue;
            HMODULE m = NULL;
            bool in_game = GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                                              (LPCSTR)(uintptr_t)ctx.Rip, &m) && m == g_game;
            add((uint32_t)i, ctx.Rip, in_game ? 0 : lr);
            th[i].samples++;
        }
        Sleep(1);
    }
    dump();
    timeEndPeriod(1);
    return 0;
}

__attribute__((constructor)) static void cpuprof_init(void) {
    const char *e = getenv("PVR_CPUPROF");
    if (!e || sscanf(e, "%lf:%lf", &t_from, &t_to) != 2 || t_to <= t_from) { t_from = -1; return; }
    CreateThread(NULL, 0, sampler, NULL, 0, NULL);
}
