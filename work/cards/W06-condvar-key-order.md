# W06 — condvar: write the key BEFORE releasing the mutex (`svc_wait_process_wide_key`)

## Bug (found by Claude with evidence; 14/10)
Pokémon Violet sometimes stops between 16 and 512 frames. All of its threads end up waiting forever.
The cause is a lost wakeup in our `svcWaitProcessWideKeyAtomic` (SVC 0x1C).

The game's `nn::os::detail::InternalConditionVariableImplByHorizon::Signal` (sdk 0x700537f9dc) **only calls the
kernel when the key is non-zero**:
```
ldr  w8, [x0]          ; w8 = *key
cbz  w8, ret           ; key == 0  -> nobody is waiting -> return WITHOUT svcSignalProcessWideKey
mov  w1, #1
b    svcSignalProcessWideKey
```
`Broadcast` (0x700537f9f0) is the same with `w1 = -1`.

Our `svc_wait_process_wide_key` (context file `W06-kernel-condvar-excerpt.c`) does:
1. `mutex_release(mutex)`: the guest mutex becomes free (or goes to the next waiter);
2. only after that, `__atomic_store_n(u32p(key), 1, ...)`.

Between 1 and 2, another host thread can run guest code that:
1. takes the (now free) mutex in user mode, with no SVC;
2. changes the shared state;
3. calls `Signal`, sees `key == 0` and does not call the kernel.

The waiter then sleeps forever. `g_klock` does not prevent this, because the signaller never enters the kernel.

## Reference: real Horizon semantics
Context file `W06-eden-condvar-reference.cpp`, function `KConditionVariable::Wait`. It is read-only: do not copy
its code, just follow the order. Inside the scheduler lock it:
1. picks the next owner of the mutex (`RemoveUserWaiterByKey`) and wakes it;
2. **writes the key = 1 (`HasWaiterFlag`), with a seq_cst fence**;
3. **only then** writes the new mutex value (next owner | waiters bit, or 0);
4. if `timeout == 0`, returns `ResultTimedOut` without waiting;
5. adds the thread to the waiter list and sleeps.

## Task
Rewrite ONLY the function `static uint32_t svc_wait_process_wide_key(uint64_t mutex, uint64_t key, uint32_t tag,
int64_t timeout)`. Output: one C file with JUST that function (no includes, no other functions). It is spliced into
`runtime/kernel.c` by `tools/workers/splice_c_function.py`.

Keep exactly the same helpers and fields as the excerpt: `pthread_mutex_lock(&g_klock)`, `t_cur`, `mutex_release`,
`u32p`, `block_current`, `t->wait_kind/wait_addr/wait_mutex/wait_tag`, `WAIT_CONDVAR`, `R_TIMEOUT`.

Required order, all while holding `g_klock`:
1. `KThread *t = t_cur;`
2. `__atomic_store_n(u32p(key), 1, __ATOMIC_SEQ_CST);` (the key FIRST)
3. `mutex_release(mutex);` (it already handles the next owner and the waiters bit)
4. if `timeout == 0`: unlock `g_klock` and return `R_TIMEOUT` (do not block)
5. set `t->wait_kind = WAIT_CONDVAR; t->wait_addr = key; t->wait_mutex = mutex; t->wait_tag = tag;`
6. `uint32_t r = block_current(timeout);`
7. **do NOT reacquire the mutex** on timeout or cancel (Horizon does not; userland `nn::os` does, see the comment
   already in the excerpt). Unlock `g_klock` and return `r`.

Keep a short comment in the function explaining why the key is written before the mutex is released (cite the Signal
`cbz` and "PVRecomp v400 hang 14/10").

## Acceptance (Claude runs it; do not claim it yourself)
- `python tools/verify/gates.py run host --version v400` (the host compiles with the spliced function);
- study: `python tools/verify/gates.py run boot --version v400 --min-stage frames_60 --seconds 45 --repeat 4`.
