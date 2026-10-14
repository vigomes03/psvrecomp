#pragma once
#include "cpu.h"

static inline void ldxp64(Cpu *c, uint64_t a, uint64_t *lo, uint64_t *hi) {
    unsigned __int128 v = __atomic_load_n((unsigned __int128 *)(uintptr_t)a, __ATOMIC_RELAXED);
    *lo = (uint64_t)v;
    *hi = (uint64_t)(v >> 64);
    c->excl_addr = a;
    c->excl_val = *lo;
    c->excl_val_hi = *hi;
}

static inline void ldaxp64(Cpu *c, uint64_t a, uint64_t *lo, uint64_t *hi) {
    unsigned __int128 v = __atomic_load_n((unsigned __int128 *)(uintptr_t)a, __ATOMIC_ACQUIRE);
    *lo = (uint64_t)v;
    *hi = (uint64_t)(v >> 64);
    c->excl_addr = a;
    c->excl_val = *lo;
    c->excl_val_hi = *hi;
}

static inline uint32_t stxp64(Cpu *c, uint64_t a, uint64_t lo, uint64_t hi) {
    if (c->excl_addr != a) return 1;
    c->excl_addr = ~0ull;
    unsigned __int128 expected = ((unsigned __int128)c->excl_val_hi << 64) | c->excl_val;
    unsigned __int128 desired = ((unsigned __int128)hi << 64) | lo;
    return !__atomic_compare_exchange_n((unsigned __int128 *)(uintptr_t)a, &expected, desired, 0, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
}

static inline uint32_t stlxp64(Cpu *c, uint64_t a, uint64_t lo, uint64_t hi) {
    if (c->excl_addr != a) return 1;
    c->excl_addr = ~0ull;
    unsigned __int128 expected = ((unsigned __int128)c->excl_val_hi << 64) | c->excl_val;
    unsigned __int128 desired = ((unsigned __int128)hi << 64) | lo;
    return !__atomic_compare_exchange_n((unsigned __int128 *)(uintptr_t)a, &expected, desired, 0, __ATOMIC_RELEASE, __ATOMIC_RELAXED);
}
