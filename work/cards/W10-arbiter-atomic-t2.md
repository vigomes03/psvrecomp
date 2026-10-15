# W10 — address arbiter: atomic read-modify-write on guest memory + Horizon wake order

## Bug (confirmed by Claude from your W09 review, items D4/D12, against Eden; 14/10)
Context `W09-kernel-sync-excerpt.c` (ours) and `W09-eden-address-arbiter.cpp` (reference, read-only).

1. **Non-atomic RMW.** `svc_wait_for_address` (DecrementAndWaitIfLessThan) does `cur = load; ... store(cur - 1)`.
   `svc_signal_to_address` does `store(cur + 1)` (IncrementIfEqual) and `store(nv)` (ModifyByWaitingCount).
   `g_klock` only serialises SVCs. **Guest user code modifies the same word concurrently with its own atomics
   (LDXR/STXR)**, so an update made between our load and our store is LOST. Eden does each of these as a
   compare-and-swap loop: `DecrementIfLessThan`, `UpdateIfEqual` (reference lines ~34-120).
2. **Wake order.** `arbiter_wake` walks `g_waitlist`, which is LIFO (`waitlist_add` pushes at the head). Horizon wakes
   the waiters of an address in **priority order (lower `prio` value first), FIFO among equal priority** (`m_tree`).

## Task
Output ONE C file with ONLY these 3 functions (spliced into `kernel.c` by `tools/workers/splice_c_function.py`;
keep the exact signatures; you may add `static` helpers, which are inserted before them):
`svc_wait_for_address`, `arbiter_wake`, `svc_signal_to_address`.

Use `__atomic_load_n` / `__atomic_compare_exchange_n(u32p(addr), &expected, desired, false, __ATOMIC_SEQ_CST,
__ATOMIC_SEQ_CST)` on the `uint32_t` word, and interpret values as `int32_t`.
- Helper `static bool dec_if_less(uint64_t addr, int32_t value, int32_t *out)`: loop
  { `cur` = load; if `cur < value`, CAS cur → cur-1 (retry on CAS failure); else break }. `*out = cur`, the value
  BEFORE the decrement. Returns true.
- Helper `static bool update_if_equal(uint64_t addr, int32_t value, int32_t new_value, int32_t *out)`: loop
  { `cur` = load; if `cur == value`, CAS cur → new_value (retry on failure); else break }. `*out = cur`.
- `svc_wait_for_address`: same checks and return codes as now, in Eden's order:
  - type 1: `dec_if_less(addr, value, &cur)`; types 0 and 2: plain load;
  - type 0/1: `cur >= value` → InvalidState; type 2: `cur != value` → InvalidState;
  - unknown type → InvalidEnum;
  - then `timeout == 0` → Timeout;
  - then wait (`t_cur->wait_kind = WAIT_ARBITER; t_cur->wait_addr = addr; block_current(timeout)`).
- `svc_signal_to_address`:
  - type 0: just wake;
  - type 1: `update_if_equal(addr, value, value + 1, &cur)`; `cur != value` → InvalidState, else wake `count`;
  - type 2: compute `new_value` exactly as now (that part matches Eden). If `new_value != value`, use
    `update_if_equal(addr, value, new_value, &cur)`; else plain load into `cur`. `cur != value` → InvalidState, else
    wake `count`.
- `arbiter_wake(addr, count)`: repeat until `count > 0 && woken >= count`:
  - pick, among the threads in `g_waitlist` with `wait_kind == WAIT_ARBITER && wait_addr == addr`, the one with the
    LOWEST `prio`. Ties go to the one waiting LONGEST: give `KThread` no new field; instead use the list order, which
    is newest-first, so among equal `prio` take the LAST matching one in the list;
  - wake it as now (`wait_kind = WAIT_NONE; wait_result = R_OK; wake(t)`);
  - stop when there is none left. Return the number woken.

Everything runs while holding `g_klock`, as today. Add a one-line comment per helper citing the reason
("guest LDXR/STXR concurrent with the kernel: CAS like Eden DecrementIfLessThan/UpdateIfEqual, PVRecomp 14/10").

## Acceptance (Claude runs it)
- `python tools/verify/gates.py run host --version v400`;
- study: `python tools/verify/gates.py run boot --version v400 --min-stage frames_60,survived_time_limit --seconds 60 --repeat 4`.

## ATTEMPT 2 — REJECTED (attempt 1 = context `arbiter_attempt1.c`; gate host v400 run_id=c69e59be66 FAIL)
`dec_if_less`, `update_if_equal`, `svc_wait_for_address` and `svc_signal_to_address` are GOOD: keep them exactly.
Rewrite ONLY `arbiter_wake` (output all 5 functions again, the other 4 unchanged):
1. `error: no member named 'wait_time' in 'struct KThread'`: there is no such field and you must not add one. For
   FIFO among equal `prio` use the list order: `g_waitlist` is newest-first, so when `it->prio == t->prio` prefer `it`
   (the later one in the list = the older waiter): condition `!t || it->prio <= t->prio`.
2. `while (count > 0 && woken < count)` wakes NOBODY when `count <= 0`, but `count <= 0` means "wake ALL".
   Loop: `for (;;) { if (count > 0 && woken >= count) break; pick t; if (!t) break; wake t; woken++; }`.
3. Delete the first loop (computes `best`, never used).
