// Guest setjmp/longjmp (PVRecomp). Lifted code calls guest functions as C calls, so a guest longjmp, which "returns"
// to the instruction after some earlier `bl setjmp`, can't be a plain return: that address is in the middle of a C
// function. gen.py emits, at every `bl setjmp` site, `if (setjmp(*rt_jmp_slot(env))) x0 = rt_jmp_value();`
// in the caller's own frame (still live while setjmp's buffer is valid), then calls the guest setjmp, which saves
// the guest registers into env as usual. The longjmp HLE below restores those guest registers from env (musl
// aarch64 layout, read from the SDK's setjmp: x19-x30 @0, sp @0x68, d8-d15 @0x70) and jumps to the checkpoint.
// CRT setjmp, not __builtin_setjmp: on Win64 clang's builtin saves llvm.frameaddress (rbp minus the frame offset),
// restoring a wrong rbp after the jump (boot 14/10: crash right after the longjmp). The CRT one unwinds via SEH.
#include <setjmp.h>
#include <stdio.h>
#include <string.h>

#include "hle.h"

#define SLOTS 256
typedef struct { uint64_t env; jmp_buf buf; } JmpSlot;
static __thread JmpSlot slots[SLOTS];
static __thread int nslots;
static __thread uint64_t jmp_value;

jmp_buf *rt_jmp_slot(uint64_t env) {
    // (PVRecomp) Drop checkpoints of frames that already returned: arming a buffer at stack address E means the
    // caller's frame is at E, so buffers of the SAME stack below E (deeper frames) are dead. Live outer buffers
    // are above E. Before, slots only left by FIFO eviction at 64: Lua's outermost protected call (armed once,
    // top of the thread stack) was evicted after 64 newer setjmps and its error longjmp died with "without a host
    // checkpoint" (Poco Path, 16/10). Buffers far from E (heap, other stacks) are left alone.
    int k = 0;
    for (int i = 0; i < nslots; i++) {
        bool dead = slots[i].env < env && env - slots[i].env < (64ull << 20);
        if (!dead) {
            if (k != i) slots[k] = slots[i];
            k++;
        }
    }
    nslots = k;
    for (int i = 0; i < nslots; i++)
        if (slots[i].env == env) return &slots[i].buf;  // re-armed (a setjmp in a loop): same guest buffer
    if (nslots == SLOTS) {  // still full (heap buffers): drop the oldest
        static int warned;
        if (!warned++) LOG("[setjmp] %d live checkpoints: dropping the oldest\n", SLOTS);
        memmove(slots, slots + 1, (SLOTS - 1) * sizeof *slots);
        nslots--;
    }
    slots[nslots].env = env;
    return &slots[nslots++].buf;
}
uint64_t rt_jmp_value(void) { return jmp_value; }

static void hle_longjmp(Cpu *c) {
    uint64_t env = c->x[0], val = c->x[1];
    JmpSlot *s = NULL;
    for (int i = 0; i < nslots; i++)
        if (slots[i].env == env) s = &slots[i];
    if (!s) FATAL("guest longjmp(%llx) without a host checkpoint (setjmp not called through a lifted bl?)\n",
                  (unsigned long long)env);
    const uint64_t *e = (const uint64_t *)(uintptr_t)env;
    for (int i = 0; i < 12; i++) c->x[19 + i] = e[i];  // x19..x30
    c->sp = e[13];                                      // @0x68
    for (int i = 0; i < 8; i++) c->v[8 + i] = e[14 + i];  // d8..d15 (upper halves are not callee-saved)
    jmp_value = val ? val : 1;
    static int logged;
    if (logged < 4) {
        logged++;
        LOG("[setjmp] guest longjmp(%llx, %llu) -> lr %llx sp %llx\n", (unsigned long long)env,
            (unsigned long long)val, (unsigned long long)c->x[30], (unsigned long long)c->sp);
    }
    longjmp(s->buf, 1);
}

// Bind every module's longjmp (guest calls reach it through PLT -> rt_dispatch, where overrides are checked).
void setjmp_install(void) {
    static const char *names[] = {"longjmp", "_longjmp", "siglongjmp"};
    for (unsigned i = 0; i < sizeof names / sizeof names[0]; i++) {
        uint64_t a = loader_find_symbol(names[i]);
        if (a) hle_override(a, hle_longjmp, names[i]);
    }
}
