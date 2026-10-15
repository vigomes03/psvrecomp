// Acceptance test for card W07 (runtime/nvn/cmdbuf.c: large commands split across command-memory chunks).
// Includes the real cmdbuf.c. The memory callback hands out 1024-byte chunks, like Violet's (boot 14/10: "need
// 1568; chunk size 1024"). Prints "W07 PASS" and exits 0 only if every check holds.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nvn/cmdbuf.c"

void rt_fatal_trace(void) {
    printf("W07 FAIL (FATAL called)\n");
    exit(1);
}

#define CALLBACK_ADDR 0x1234
#define CHUNK 1024
static uint8_t *g_storage;
static uint64_t g_next, g_pool_obj, g_cb_obj[8];
static NvnPool g_pool;
static int g_callbacks;

void guest_call(Cpu *c, uint64_t addr) {  // the game's out-of-memory callback: AddCommandMemory(cb, pool, off, 1024)
    if (addr != CALLBACK_ADDR) { printf("W07 FAIL (unexpected guest_call %llx)\n", (unsigned long long)addr); exit(1); }
    g_callbacks++;
    Cpu k = *c;
    k.x[0] = c->x[0];
    k.x[1] = (uint64_t)(uintptr_t)&g_pool_obj;
    k.x[2] = g_next;
    k.x[3] = CHUNK;
    g_next += CHUNK;
    hle_nvnCommandBufferAddCommandMemory(&k);
}

static int fails;
#define CHECK(x) do { if (!(x)) { printf("FAIL line %d: %s\n", __LINE__, #x); fails++; } } while (0)

// Walk a recorded list (follow CMD_JUMP, stop at CMD_END). Calls fn for every record.
static void walk(uint64_t start, void (*fn)(CmdRec *)) {
    uint64_t at = start;
    for (int guard = 0; guard < 100000; guard++) {
        CmdRec *r = (CmdRec *)(uintptr_t)at;
        CHECK(r->size >= sizeof(CmdRec) && r->size % 8 == 0);
        CHECK(r->size + JUMP_RESERVE <= CHUNK);  // every record fits a chunk the game gives
        if (r->op == CMD_END) return;
        if (r->op == CMD_JUMP) { at = r->x[0]; continue; }
        fn(r);
        at += r->size;
    }
    CHECK(!"list did not end");
}

static uint8_t got_ubo[4096], got_calls[4096];
static uint64_t ubo_next_off, ubo_total, calls_total;
static int ubo_recs, call_recs;
static void on_rec(CmdRec *r) {
    if (r->op == CMD_UPDATE_UNIFORM_BUFFER) {
        // x[] = call x1..x7: buffer, bufferSize, updateOffset, updateSize, data
        CHECK(r->x[0] == 0xABC000 && r->x[1] == 0x10000);
        CHECK(r->x[2] == ubo_next_off);  // pieces are contiguous and in order
        CHECK(r->x[3] > 0 && ubo_total + r->x[3] <= sizeof got_ubo);
        memcpy(got_ubo + ubo_total, r->extra, r->x[3]);
        ubo_next_off += r->x[3];
        ubo_total += r->x[3];
        ubo_recs++;
    } else if (r->op == CMD_CALL) {
        // x[] = count, handles
        CHECK(r->x[0] > 0 && calls_total + r->x[0] * 8 <= sizeof got_calls);
        memcpy(got_calls + calls_total, r->extra, r->x[0] * 8);
        calls_total += r->x[0] * 8;
        call_recs++;
    }
}

int main(void) {
    g_storage = calloc(1, 1 << 20);
    g_pool.storage = (uint64_t)(uintptr_t)g_storage;
    g_pool.size = 1 << 20;
    g_pool_obj = (uint64_t)(uintptr_t)&g_pool;
    Cpu c;
    memset(&c, 0, sizeof c);
    c.x[0] = (uint64_t)(uintptr_t)g_cb_obj;
    hle_nvnCommandBufferInitialize(&c);
    c.x[0] = (uint64_t)(uintptr_t)g_cb_obj;
    c.x[1] = CALLBACK_ADDR;
    hle_nvnCommandBufferSetMemoryCallback(&c);
    c.x[0] = (uint64_t)(uintptr_t)g_cb_obj;
    hle_nvnCommandBufferBeginRecording(&c);

    uint8_t ubo[1488];  // the size seen in the v400 boot
    for (unsigned i = 0; i < sizeof ubo; i++) ubo[i] = (uint8_t)(i * 7 + 3);
    memset(&c, 0, sizeof c);
    c.x[0] = (uint64_t)(uintptr_t)g_cb_obj;
    c.x[1] = 0xABC000; c.x[2] = 0x10000; c.x[3] = 0x40; c.x[4] = sizeof ubo; c.x[5] = (uint64_t)(uintptr_t)ubo;
    hle_nvnCommandBufferUpdateUniformBuffer(&c);
    CHECK(c.x[0] == (uint64_t)(uintptr_t)g_cb_obj && c.x[5] == (uint64_t)(uintptr_t)ubo);  // caller regs preserved

    uint64_t handles[200];
    for (int i = 0; i < 200; i++) handles[i] = 0x7000000000ull + (uint64_t)i * 0x40;
    memset(&c, 0, sizeof c);
    c.x[0] = (uint64_t)(uintptr_t)g_cb_obj; c.x[1] = 200; c.x[2] = (uint64_t)(uintptr_t)handles;
    hle_nvnCommandBufferCallCommands(&c);

    uint8_t small[64];
    memset(small, 0x5A, sizeof small);
    memset(&c, 0, sizeof c);
    c.x[0] = (uint64_t)(uintptr_t)g_cb_obj;
    c.x[1] = 0xABC000; c.x[2] = 0x10000; c.x[3] = 0x40 + sizeof ubo; c.x[4] = sizeof small;
    c.x[5] = (uint64_t)(uintptr_t)small;
    hle_nvnCommandBufferUpdateUniformBuffer(&c);  // a small update stays ONE record

    c.x[0] = (uint64_t)(uintptr_t)g_cb_obj;
    hle_nvnCommandBufferEndRecording(&c);
    uint64_t start = c.x[0];

    ubo_next_off = 0x40;
    walk(start, on_rec);
    CHECK(ubo_total == sizeof ubo + sizeof small);
    CHECK(memcmp(got_ubo, ubo, sizeof ubo) == 0);
    CHECK(memcmp(got_ubo + sizeof ubo, small, sizeof small) == 0);
    CHECK(ubo_recs >= 3);  // 1488 bytes do not fit one 1024-byte chunk: split (+1 for the small one)
    CHECK(calls_total == sizeof handles && memcmp(got_calls, handles, sizeof handles) == 0);
    CHECK(call_recs >= 2);
    CHECK(g_callbacks >= 3);
    printf(fails ? "W07 FAIL (%d)\n" : "W07 PASS (%d ubo records, %d call records, %d chunks)\n",
           fails ? fails : ubo_recs, call_recs, g_callbacks);
    return fails != 0;
}
