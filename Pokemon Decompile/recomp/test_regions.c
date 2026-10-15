// Acceptance test for card W08 (runtime/regions.c, API in runtime/regions.h). Checks the interval-map invariants
// against a byte-granular reference model on random operations, plus the SDK 13 VAMM pattern that overflowed the
// old list. Prints "W08 PASS" and exits 0 only if every check holds.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "regions.h"

static int fails;
#define CHECK(x) do { if (!(x)) { printf("FAIL line %d: %s\n", __LINE__, #x); if (++fails > 20) exit(1); } } while (0)

// invariants: sorted, non-overlapping, non-empty, adjacent regions differ in type/perm
static void check_invariants(void) {
    int n = regions_count();
    for (int i = 0; i < n; i++) {
        const Region *r = regions_at(i);
        CHECK(r && r->size > 0);
        if (i > 0) {
            const Region *p = regions_at(i - 1);
            CHECK(p->addr + p->size <= r->addr);
            if (p->addr + p->size == r->addr) CHECK(p->type != r->type || p->perm != r->perm);
        }
    }
    CHECK(regions_at(n) == NULL && regions_at(-1) == NULL);
}

// reference model over a small page space: one (type, perm) per page; type 0 = unmapped
#define PAGES 256
#define PG 0x1000ull
#define BASE 0x7100000000ull
static uint32_t ref_type[PAGES], ref_perm[PAGES];

static void compare_model(void) {
    for (int p = 0; p < PAGES; p++) {
        const Region *r = regions_find(BASE + p * PG + 0x10);
        if (ref_type[p] == 0) CHECK(r == NULL);
        else {
            CHECK(r != NULL);
            if (r) CHECK(r->type == ref_type[p] && r->perm == ref_perm[p] && r->addr <= BASE + p * PG &&
                         r->addr + r->size >= BASE + (p + 1) * PG);
        }
    }
    // region count must equal the number of maximal runs in the model (merging is complete)
    int runs = 0;
    for (int p = 0; p < PAGES; p++)
        if (ref_type[p] && (p == 0 || ref_type[p - 1] != ref_type[p] || ref_perm[p - 1] != ref_perm[p])) runs++;
    CHECK(regions_count() == runs);
}

int main(void) {
    regions_reset();
    CHECK(regions_count() == 0 && regions_find(0x1234) == NULL);

    // basic split / carve / merge
    CHECK(regions_set(0x10000, 0x10000, 7, 3) == 0);
    CHECK(regions_set(0x14000, 0x1000, 5, 1) == 0);  // middle overwrite -> 3 regions
    CHECK(regions_count() == 3);
    CHECK(regions_find(0x14800)->type == 5 && regions_find(0x13fff)->type == 7 && regions_find(0x15000)->type == 7);
    CHECK(regions_set(0x14000, 0x1000, 7, 3) == 0);  // back to one merged region
    CHECK(regions_count() == 1 && regions_at(0)->addr == 0x10000 && regions_at(0)->size == 0x10000);
    regions_clear(0x18000, 0x2000);                  // hole in the middle -> 2 regions
    CHECK(regions_count() == 2 && regions_find(0x18000) == NULL && regions_find(0x19fff) == NULL);
    CHECK(regions_find(0x17fff) && regions_find(0x1a000));
    regions_clear(0, 0x100000);                      // clear everything
    CHECK(regions_count() == 0);
    check_invariants();

    // SDK 13 VAMM pattern (boot 14/10): map a 4 KiB page, then the whole 2 MiB block around it, then unmap the block
    // in pieces; repeated many times the map must stay bounded (the old list hit 1024 entries)
    for (int it = 0; it < 20000; it++) {
        uint64_t blk = 0x7400000000ull + (uint64_t)(it % 64) * 0x200000;
        CHECK(regions_set(blk + 0x3000, 0x1000, 7, 3) == 0);
        CHECK(regions_set(blk, 0x200000, 7, 3) == 0);
        regions_clear(blk, 0x100000);
        regions_clear(blk + 0x100000, 0x100000);
        if (fails) break;
    }
    CHECK(regions_count() == 0);

    // random ops vs the page model
    srand(12345);
    regions_reset();
    memset(ref_type, 0, sizeof ref_type);
    for (int it = 0; it < 30000 && !fails; it++) {
        int p0 = rand() % PAGES, len = 1 + rand() % 24;
        if (p0 + len > PAGES) len = PAGES - p0;
        if (rand() % 3) {
            uint32_t ty = 1 + rand() % 3, pe = 1 + rand() % 2;
            CHECK(regions_set(BASE + p0 * PG, len * PG, ty, pe) == 0);
            for (int p = p0; p < p0 + len; p++) { ref_type[p] = ty; ref_perm[p] = pe; }
        } else {
            regions_clear(BASE + p0 * PG, len * PG);
            for (int p = p0; p < p0 + len; p++) ref_type[p] = 0;
        }
        if (it % 97 == 0) { check_invariants(); compare_model(); }
    }
    check_invariants();
    compare_model();

    // capacity: a full map refuses and stays unchanged
    regions_reset();
    int ok = 1;
    for (int i = 0; i < REGIONS_MAX && ok; i++) ok = regions_set(0x100000ull + i * 0x2000ull, 0x1000, 1 + i % 2, 3) == 0;
    CHECK(ok && regions_count() == REGIONS_MAX);
    CHECK(regions_set(0x900000000ull, 0x1000, 4, 3) == -1 && regions_count() == REGIONS_MAX);

    printf(fails ? "W08 FAIL (%d)\n" : "W08 PASS\n", fails);
    return fails != 0;
}
