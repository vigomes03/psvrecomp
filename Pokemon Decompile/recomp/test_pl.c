// Acceptance test for card W05 (runtime/services/pl.c): includes the service with stubbed runtime pieces.
// Usage: test_pl.exe <temp dir>   (writes 0.ttf / 1.ttf there and sets PVR_SYSFONT_DIR)
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ipc.h"
#include "kernel.h"

static void (*g_on_map)(KSharedMem *);
static KSharedMem g_shm;
KSharedMem *kernel_create_shared_memory(uint64_t size, void (*on_map)(KSharedMem *), uint32_t *handle) {
    g_shm.size = size;
    g_on_map = on_map;
    *handle = 0x1234;
    return &g_shm;
}

#include "services/pl.c"

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

static void call(uint32_t cmd, uint64_t raw_in, IpcResp *resp, IpcReq *req) {
    static uint8_t in[16];
    memcpy(in, &raw_in, 8);
    req->cmd = cmd;
    req->data = in;
    req->data_size = 8;
    memset(resp, 0, sizeof *resp);
    pl_u(NULL, req, resp);
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    char p[512];
    uint8_t f0[100], f1[7];
    for (int i = 0; i < 100; i++) f0[i] = (uint8_t)(i * 3 + 1);
    for (int i = 0; i < 7; i++) f1[i] = (uint8_t)(0xA0 + i);
    snprintf(p, sizeof p, "%s/0.ttf", argv[1]);
    FILE *f = fopen(p, "wb"); fwrite(f0, 1, 100, f); fclose(f);
    snprintf(p, sizeof p, "%s/1.ttf", argv[1]);
    f = fopen(p, "wb"); fwrite(f1, 1, 7, f); fclose(f);
    char env[600];
    snprintf(env, sizeof env, "PVR_SYSFONT_DIR=%s", argv[1]);
    putenv(env);

    IpcReq req = {0};
    IpcResp resp;
    call(1, 0, &resp, &req); CHECK(*(uint32_t *)resp.data == 1 && resp.data_size >= 4);
    call(2, 0, &resp, &req); CHECK(*(uint32_t *)resp.data == 100);
    call(2, 1, &resp, &req); CHECK(*(uint32_t *)resp.data == 7);
    call(2, 2, &resp, &req); CHECK(*(uint32_t *)resp.data == 0);
    call(3, 0, &resp, &req); CHECK(*(uint32_t *)resp.data == 8);
    call(3, 1, &resp, &req); CHECK(*(uint32_t *)resp.data == 116);

    // cmd 5: three output buffers of 6 u32 each
    uint32_t codes[6], offs[6], sizes[6];
    memset(codes, 0xEE, sizeof codes); memset(offs, 0xEE, sizeof offs); memset(sizes, 0xEE, sizeof sizes);
    IpcReq r5 = {0};
    r5.nb = 3;
    r5.b[0].addr = (uint64_t)(uintptr_t)codes; r5.b[0].size = sizeof codes;
    r5.b[1].addr = (uint64_t)(uintptr_t)offs; r5.b[1].size = sizeof offs;
    r5.b[2].addr = (uint64_t)(uintptr_t)sizes; r5.b[2].size = sizeof sizes;
    call(5, 0x53552d6e65ull, &resp, &r5);
    CHECK(resp.data[0] == 1);
    CHECK(*(uint32_t *)(resp.data + 4) == 6);
    CHECK(resp.data_size >= 8);
    CHECK(codes[0] == 0 && codes[1] == 1 && codes[5] == 5);
    CHECK(offs[0] == 8 && offs[1] == 116 && sizes[0] == 100 && sizes[1] == 7 && sizes[2] == 0);

    // cmd 4: handle + mapping copies the block with headers and bytes
    call(4, 0, &resp, &req);
    CHECK(resp.ncopy == 1 && resp.copy_handles[0] == 0x1234);
    CHECK(g_on_map != NULL && g_shm.size == 0x1100000);
    uint8_t *guest = calloc(1, 0x1100000);
    g_shm.guest_addr = (uint64_t)(uintptr_t)guest;
    if (g_on_map) g_on_map(&g_shm);
    CHECK(*(uint32_t *)guest == 0x18029a7f);
    CHECK(*(uint32_t *)(guest + 4) == (100u ^ 0x49621806u));
    CHECK(memcmp(guest + 8, f0, 100) == 0);
    CHECK(*(uint32_t *)(guest + 108) == 0x18029a7f);
    CHECK(*(uint32_t *)(guest + 112) == (7u ^ 0x49621806u));
    CHECK(memcmp(guest + 116, f1, 7) == 0);
    printf(fails ? "W05 FAIL (%d)\n" : "W05 PASS\n", fails);
    return fails != 0;
}
