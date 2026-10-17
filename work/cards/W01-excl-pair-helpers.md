# W01: C helpers for 64-bit pair exclusives (LDXP/LDAXP/STXP/STLXP)

## Goal
Write the file `runtime/excl_pair.h` with 4 `static inline` functions that emulate AArch64 pair exclusive accesses
(128 bits) on the x86-64 PC, in the same style as the single exclusives that already exist in `cpu.h`.

## API that ALREADY EXISTS (do not declare it again; include "cpu.h")
```c
typedef struct Cpu {
    uint64_t x[32]; uint64_t sp; uint64_t pc; uint64_t nzcv; uint64_t tpidr; uint64_t tpidrro;
    uint64_t excl_addr;     // address reserved by the last exclusive load; ~0ull = no reservation
    uint64_t excl_val;      // value read by the exclusive load (LOW half, bytes a..a+7)
    void *thread; uint64_t fpcr; uint64_t fpsr;
    uint64_t excl_val_hi;   // HIGH half (bytes a+8..a+15)
    ...
} Cpu;
```
Existing pattern for 64 bits (copy the logic, not the macro):
```c
static inline uint64_t ldx64(Cpu *c, uint64_t a) {
    uint64_t v = __atomic_load_n((uint64_t *)(uintptr_t)a, __ATOMIC_ACQUIRE);
    c->excl_addr = a; c->excl_val = v; return v; }
static inline uint32_t stx64(Cpu *c, uint64_t a, uint64_t v) {
    if (c->excl_addr != a) return 1;
    c->excl_addr = ~0ull;
    uint64_t expected = c->excl_val;
    return !__atomic_compare_exchange_n((uint64_t *)(uintptr_t)a, &expected, v, 0, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST); }
```

## What to write (exactly these 4 signatures)
```c
#pragma once
#include "cpu.h"
// exclusive load in pair: *lo = mem[a..a+7], *hi = mem[a+8..a+15]; reserve the monitor
static inline void ldxp64(Cpu *c, uint64_t a, uint64_t *lo, uint64_t *hi);
// same, with acquire semantics (LDAXP)
static inline void ldaxp64(Cpu *c, uint64_t a, uint64_t *lo, uint64_t *hi);
// exclusive store in pair: returns 0 if wrote lo/hi, 1 if failed (different reservation or memory changed)
static inline uint32_t stxp64(Cpu *c, uint64_t a, uint64_t lo, uint64_t hi);
// same, with release semantics (STLXP)
static inline uint32_t stlxp64(Cpu *c, uint64_t a, uint64_t lo, uint64_t hi);
```
Rules:
- Use `unsigned __int128` and `__atomic_load_n` / `__atomic_compare_exchange_n` of 16 bytes (the address is aligned to 16).
- Value of 128 bits = `(unsigned __int128)hi << 64 | lo` (little-endian: `lo` goes at the lower address).
- On load: `c->excl_addr = a; c->excl_val = lo; c->excl_val_hi = hi;`.
- On store: if `c->excl_addr != a` return 1 without writing; otherwise zero the reservation (`c->excl_addr = ~0ull`) and do CAS
  comparing with `(excl_val_hi, excl_val)`; return 0 if the CAS wrote, 1 if not.
- Nothing beyond the 4 functions and the `#pragma once` / `#include`.

## Accept (Claude runs)
1. Compile with `clang -O1 -march=x86-64-v3` without warnings, and **without** depending on `libatomic` (link to a test without `-latomic`).
2. Test: `ldxp64` reads the two correct values; `stxp64` immediately returns 0 and writes; second `stxp64` without new load
   returns 1; `stxp64` after another thread changes memory returns 1 and does not write.
