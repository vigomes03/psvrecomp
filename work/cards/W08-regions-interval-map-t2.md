# W08 — guest memory map as an interval map (`runtime/regions.c`)

## Bug (found by Claude with evidence; 14/10)
The base boot (v1.0.0) now reaches 256 frames 4 times out of 4 and then always dies with `FATAL: too many regions`.
The kernel keeps the guest memory map (`svcQueryMemory`) in a flat list of 1024 `Region`:
- `region_add` only appends;
- `region_remove(addr)` only removes an entry that starts at exactly `addr`.

The SDK 13 VAMM breaks both:
- `MapPhysicalMemory` maps a 4 KiB page and then the whole block around it, so the entries overlap;
- `UnmapPhysicalMemory` unmaps pieces that don't match any entry's start.

The list only grows.

## Reference (semantics)
Horizon keeps the address space as a block tree (`KMemoryBlockManager`): every address belongs to exactly one block,
and an operation on a range **splits** the blocks at the range's edges and **coalesces** neighbours with the same
state (`KMemoryBlockManager::Update` + `CoalesceForUpdate` in Atmosphère's mesosphere /
`src/core/hle/kernel/k_memory_block_manager.cpp` in Eden, `D:\Dev\REA\ref\eden-master`; read only, don't copy).
We need the same thing, simplified: a sorted array of non-overlapping intervals.

## Task
Write `runtime/regions.c` implementing EXACTLY the API in `runtime/regions.h` (context; do not change the header).
Pure C11, only `<stdint.h>`, `<string.h>` and `"regions.h"`; no malloc, no kernel.
- Storage: `static Region g_regions[REGIONS_MAX]; static int g_n;`, kept **sorted by addr** with **no overlaps** and no
  `size == 0`.
- `regions_reset()`: `g_n = 0`.
- `regions_clear(addr, size)`: for each region overlapping `[addr, end)` (end = addr + size):
  - fully covered: remove it;
  - covers only its left part: move the start to `end`;
  - covers only its right part: cut it at `addr`;
  - **strictly inside** the region: split it in two (left part `[r.addr, addr)` and right part `[end, r.end)`).
  If the split doesn't fit (`g_n == REGIONS_MAX`), keep only the left part (never write past the array).
  `size == 0` does nothing.
- `regions_set(addr, size, type, perm)`:
  - first check capacity. Worst case it needs +2 slots: one for the new region and one for a split. If
    `g_n + 2 > REGIONS_MAX`, return -1 **without changing anything**. Exception: return 0 normally if the operation
    doesn't create a net slot (simplest correct rule: copy the state, try, and roll back if it overflows).
  - then `regions_clear(addr, size)`, insert `{addr, size, type, perm}` in order (memmove), and **merge** with the left
    neighbour if `left.addr + left.size == addr` and type/perm are the same, and the same with the right neighbour.
    Return 0.
- `regions_count()`, `regions_at(i)` (NULL if i < 0 or i >= count), `regions_find(addr)` (binary or linear search;
  NULL if no region contains addr).

The test's invariants: sorted; non-overlapping; touching neighbours always differ in type or perm (merging complete);
the number of regions equals the number of maximal runs in a per-page model.

## Acceptance (Claude runs it; do not claim it yourself)
`python tools/verify/gates.py run regions`: `recomp/test_regions.c` (context) compiled with `-Wall -Werror`. It runs:
- split/carve/merge cases;
- 20000 cycles of the VAMM pattern;
- 30000 random operations compared with a per-page model;
- the capacity test (full → -1 and nothing changes).

It must print `W08 PASS`. The integration into `kernel.c` is done by Claude afterwards.

## ATTEMPT 2 — REJECTED (attempt 1, context `regions_attempt1.c`: gate regions run_id=6b20b91871 FAIL)
Test failures: line 59 `regions_count() == 3` (set 0x14000+0x1000 in the MIDDLE of 0x10000+0x10000 did not split),
lines 60/62/64 consequences. Rewrite the file fixing exactly these 3 errors:
1. `regions_clear` starts the loop at `find_insert_pos(addr)` = first region with `start >= addr`. That SKIPS the
   region that starts BEFORE `addr` and overlaps it (the "strictly inside" and "covers its right part" cases never
   run). Start at `i = find_insert_pos(addr); if (i > 0 && g_regions[i-1].addr + g_regions[i-1].size > addr) i--;`.
2. In `regions_set`, after `merge_left(pos)` merges, the new region is at `pos - 1`, not `pos`; `merge_right(pos)`
   then looks at the wrong index. Make `merge_left` return the new index (`i - 1` if it merged, else `i`) and call
   `merge_right` on that index.
3. Replace the whole capacity logic (lines 103-150) with the simple, exact rule: snapshot, try, roll back:
   `static Region backup[REGIONS_MAX];` — if `g_n + 2 > REGIONS_MAX`: `memcpy(backup, g_regions, g_n * sizeof(Region));
   int bn = g_n;` then do the operation; if at any point an insert would need `g_n == REGIONS_MAX`, restore
   (`memcpy` back, `g_n = bn`) and return -1. When `g_n + 2 <= REGIONS_MAX` no backup is needed.
   In `regions_clear`, a split with `g_n == REGIONS_MAX` must report it (make an internal
   `static int clear_impl(uint64_t addr, uint64_t size)` that returns -1 on that case; the public `regions_clear`
   calls it and, on -1, keeps only the left part as before).
Keep everything else (API, binary search in `find_region`, merges).
