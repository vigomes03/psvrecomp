// PVRecomp headless host (fase 2): load pvgame.dll and the NSOs, set up the kernel, run nn::init::Start on the main
// thread. No window, no audio: graphics/audio entry points are stubs that log. Adapted from LAS Recomp main.c (MIT).
// Usage: pvhost.exe <exefs_dir> [romfs_dir]     env: PVR_RUN_SECONDS (default 60), PVR_GAMELIB (default pvgame.dll)
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

#include "hle.h"
#include "kernel.h"
#include "pvgame.h"

const char *g_romfs_dir;
static const PvGameTables *g_tables;
const PvGameTables *pvgame_tables_loaded(void) { return g_tables; }

static void load_pvgame(void) {
    const char *dll = getenv("PVR_GAMELIB") ? getenv("PVR_GAMELIB") : PVGAME_NAME;
    HMODULE h = LoadLibraryA(dll);
    if (!h) FATAL("LoadLibrary(%s) failed: %lu\n", dll, GetLastError());
    PvGameEntry e = (PvGameEntry)(void *)GetProcAddress(h, PVGAME_ENTRY);
    if (!e) FATAL("%s: no %s\n", dll, PVGAME_ENTRY);
    g_tables = e();
    if (g_tables->abi != PVGAME_ABI) FATAL("%s: abi %u != %u\n", dll, g_tables->abi, PVGAME_ABI);
    uint64_t n = 0;
    for (uint32_t i = 0; i < g_tables->nmods; i++) n += *g_tables->mods[i].count;
    LOG("pvgame: %s, %u modules, %llu functions\n", g_tables->id, g_tables->nmods, (unsigned long long)n);
}

// rtld normally passes these to nn::init::Start: run each module's DT_INIT (or its init_array).
static void run_array(Cpu *c, uint64_t arr, uint64_t size) {
    for (uint64_t i = 0; i < size / 8; i++) {
        uint64_t fn = ((uint64_t *)arr)[i];
        if (fn) guest_call(c, fn);
    }
}
static void module_init(Cpu *c, Module *m) {
    LOG("init %s (DT_INIT %llx, %llu init_array entries)\n", m->name, (unsigned long long)m->init,
        (unsigned long long)(m->init_array_sz / 8));
    if (m->init) guest_call(c, m->init);
    else run_array(c, m->init_array, m->init_array_sz);
}
// x2 (after nnosInitialize) runs nothing: Pokémon's sdk constructors (iostream init -> the game's own malloc, which
// keeps its allocator in main's TLS) need the heap and the thread-local allocator that nninitStartup sets up, and
// __nnmusl_init_dso skips the TLS/thread-pointer setup while nn::os::MemoryAllocatorForThreadLocalInitialized() is
// false (boot probe 14/10: sdk DT_INIT at x2 -> tpidr 0 -> fault at 0x20). So every DT_INIT runs at x3, after
// nninitStartup, dependencies first: sdk, subsdk0, then the game. PVR_INIT_AT_X2=1 restores the LAS order.
static void rtld_init_sdk(Cpu *c) {
    if (getenv("PVR_INIT_AT_X2")) { module_init(c, &g_modules[2]); module_init(c, &g_modules[1]); }
}
static void rtld_init_main(Cpu *c) {
    if (!getenv("PVR_INIT_AT_X2")) { module_init(c, &g_modules[2]); module_init(c, &g_modules[1]); }
    module_init(c, &g_modules[0]);
}
static void rtld_fini(Cpu *c) { (void)c; LOG("[pvhost] nnMain returned (fini)\n"); }

// Claim the guest address range before anything else can map there.
__attribute__((constructor(101))) static void reserve_guest_space(void) {
    if (!plat_reserve_guest(GUEST_LO, GUEST_HI)) {
        fprintf(stderr, "FATAL: guest address range %llx-%llx is not free\n", (unsigned long long)GUEST_LO,
                (unsigned long long)GUEST_HI);
        exit(1);
    }
}

// PE/COFF: .rst$a < .rst$m (RT_ON_RESET entries, hle.h) < .rst$z. Headless never reboots, but keep the markers.
__attribute__((section(".rst$a"), used)) static const ResetFn __start_resets[1];
__attribute__((section(".rst$z"), used)) static const ResetFn __stop_resets[1];

// Reboot is not used headless; kernel.c still references these.
static _Atomic int g_reboot;
void rt_request_reboot(int kind) { g_reboot = kind; }
int rt_reboot_requested(void) { return g_reboot; }

#ifdef PVR_VULKAN
static DWORD WINAPI run_limit_thread(LPVOID p) {  // window mode: end the run after PVR_RUN_SECONDS (same log line)
    Sleep((DWORD)*(int *)p * 1000);
    LOG("[pvhost] time limit reached, exiting\n");
    if (getenv("PVR_DUMP_THREADS")) { extern void kernel_dump_threads(void); kernel_dump_threads(); }
    plat_terminate();
    return 0;
}
#endif

int main(int argc, char **argv) {
    plat_init();
    setvbuf(stderr, NULL, _IONBF, 0);
    if (argc < 2) { fprintf(stderr, "usage: %s <exefs_dir> [romfs_dir]\n", argv[0]); return 2; }
    const char *exefs = argv[1];
    g_romfs_dir = argc > 2 ? argv[2] : NULL;
    load_pvgame();
    loader_load(exefs);
    kernel_init();
    dispatch_init();
    { extern void setjmp_install(void); setjmp_install(); }  // guest longjmp -> host checkpoint (setjmp.c)
    { extern void diag_install(void); diag_install(); }  // log nn::diag aborts with their strings (diag_log.c)

    uint32_t stack_size = 0x100000;
    int prio = 44;
    char npdm[1024];
    snprintf(npdm, sizeof npdm, "%s/main.npdm", exefs);
    FILE *f = fopen(npdm, "rb");
    if (f) {
        uint8_t meta[0x80];
        if (fread(meta, 1, sizeof meta, f) == sizeof meta && !memcmp(meta, "META", 4)) {
            prio = meta[0xE];
            stack_size = *(uint32_t *)(meta + 0x1C);
        }
        fclose(f);
    }
    LOG("main thread: prio %d, stack 0x%x\n", prio, stack_size);
    // SDK 13.3.5: nn::init::Start(thread, args, init_sdk, init_main, fini). It runs: _init_libc0, nnosInitialize,
    // x2, _init_libc1, nninitInitializeSdkModule, nninitStartup, _init_libc2, x3, nnMain, x4, nninitFinalizeSdkModule,
    // nnosQuickExit.
    uint64_t start = loader_find_symbol("_ZN2nn4init5StartEmmPFvvES2_S2_");
    if (!start) FATAL("nn::init::Start (SDK 13 signature) not found\n");
    uint64_t init_sdk = hle_register("<rtld_init_sdk>", rtld_init_sdk);
    uint64_t init_main = hle_register("<rtld_init_main>", rtld_init_main);
    uint64_t fini = hle_register("<rtld_fini>", rtld_fini);
    KThread *t = kernel_create_main_thread(start, stack_size, prio);
    kernel_run_main(t, t->handle, 0, init_sdk, init_main, fini);

    int secs = getenv("PVR_RUN_SECONDS") ? atoi(getenv("PVR_RUN_SECONDS")) : 60;
#ifdef PVR_VULKAN
    // Window build: the main thread owns the SDL window + event loop (ui_run creates the window and the Vulkan device,
    // then the guest's backend_init stops waiting). PVR_RUN_SECONDS > 0 still ends the run, from a timer thread.
    if (secs > 0) {
        static int limit;
        limit = secs;
        CreateThread(NULL, 0, run_limit_thread, &limit, 0, NULL);
    }
    LOG("[pvhost] window mode (Vulkan), %d s limit\n", secs);
    extern int ui_run(void);
    ui_run();
    return 0;
#endif
    LOG("[pvhost] running headless for %d s\n", secs);
    Sleep((DWORD)secs * 1000);
    LOG("[pvhost] time limit reached, exiting\n");
    if (getenv("PVR_DUMP_THREADS")) { extern void kernel_dump_threads(void); kernel_dump_threads(); }
    plat_terminate();
    return 0;
}
