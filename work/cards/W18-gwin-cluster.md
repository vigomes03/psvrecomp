# W18 — Group GPU memory pools into memory windows (pure function + test)

## Context
The game creates hundreds of NVN memory pools scattered across ~11 GB of addresses (two large groups). The Vulkan backend
imports guest memory in "windows" that are contiguous (up to 8, each < 4 GB). We need a pure function
that, given the list of pools, returns the windows.

## Deliverables: two files
1. `gwin.c` with the function (no dependencies beyond `<stdint.h>`, `<stdlib.h>`, `<string.h>`):
```c
typedef struct { uint64_t base, size; } GwinRange;
// pools: n ranges [base, base+size) any (unordered, may overlap, size > 0).
// Output: windows sorted by base, no overlap, each one:
//   base aligned DOWN to `align`, end aligned UP to `align` (align is power of 2);
//   covers all pools that fall into it;
// Two aligned ranges join into a single window if the distance between them (start of 2nd - end of 1st) is <= gap
// And the resulting window has size <= maxspan. Ranges that touch or overlap always join if they fit.
// A pool that alone (aligned) exceeds maxspan becomes its own window anyway.
// Returns the number of windows written to out; if more than maxout would be needed, returns -1.
int gwin_cluster(const GwinRange *pools, int n, uint64_t align, uint64_t gap, uint64_t maxspan,
                 GwinRange *out, int maxout);
```
Suggested algorithm: copy, align each range, sort by base (qsort), scan joining while rules allow.

2. `test_gwin.c` with `main()` that tests and prints `PASS n` or `FAIL <caso>` (returns 0 only if all pass):
| case | pools (base, size) | align, gap, maxspan, maxout | expected windows (base, size) |
|---|---|---|---|
| empty | — | 0x4000000, 0x20000000, 0xF0000000, 8 | 0 windows |
| one | (0x7441c8f000, 0x10000) | 0x4000000, 0x20000000, 0xF0000000, 8 | (0x7440000000, 0x4000000) |
| two close | (0x7441c8f000, 0x10000), (0x7449900000, 0x100000) | same | (0x7440000000, 0xC000000) |
| two far | (0x7441c8f000, 0x10000), (0x76c9c00000, 0x1000) | same | (0x7440000000, 0x4000000), (0x76c8000000, 0x4000000) |
| disordered | (0x76c9c00000, 0x1000), (0x7441c8f000, 0x10000) | same | same as "two far" |
| maxspan | (0x0, 0x1000), (0x10000000, 0x1000) | 0x1000000, 0x20000000, 0x8000000, 8 | (0x0, 0x1000000), (0x10000000, 0x1000000) |
| maxout | 3 pools at 0x0, 0x40000000, 0x80000000 (size 0x1000) | 0x1000000, 0x1000000, 0xF0000000, 2 | return -1 |

## Acceptance (Claude runs)
`clang -O2 -Wall gwin.c test_gwin.c -o test_gwin.exe && ./test_gwin.exe` prints `PASS 7` and returns 0, without warnings.
Do not invent cases with different values from the table.
