# W09 — REVIEW: our kernel sync SVCs vs Horizon (Eden reference). Output = findings list, no code.

## Why
Pokémon Violet v4.0.0 fails at random (1 run in 3-8):
- a Lua script error `attempt to index a nil value` in an event coroutine at frame 16;
- or a null dereference at frame 512.

Three races in this same kernel code (inherited from LAS Recomp) were already found and fixed today:
(a) on timeout, condvar wait must NOT reacquire the mutex;
(b) a wake that races a timeout must keep success;
(c) only WaitSynchronization/arbiter may consume CancelSynchronization;
(d) the condvar key must be written BEFORE the mutex is released, because nn::os `Signal` skips the SVC when key == 0.
More of the same kind probably remain.

## Inputs (context)
- `W09-kernel-sync-excerpt.c`: OUR code (mutex: `svc_arbitrate_lock/unlock`, `mutex_release`, `mutex_acquire_or_mark`;
  condvar: `svc_wait_process_wide_key`, `svc_signal_process_wide_key`; arbiter: `svc_wait_for_address`,
  `svc_signal_to_address`; `svc_wait_synchronization`, `block_current`). All of it runs under one global lock
  `g_klock`, and a waiter sleeps on its own pthread cond.
- `W09-eden-address-arbiter.cpp` and `W09-eden-condvar.cpp`: Eden's implementation = the real Horizon semantics
  (read-only reference).

SVC ABI (Horizon): `WaitForAddress(addr, ArbitrationType, value, timeout)` with types
0 = WaitIfLessThan, 1 = DecrementAndWaitIfLessThan, 2 = WaitIfEqual, 3 = WaitIfEqual64 (newer kernels).
`SignalToAddress(addr, SignalType, value, count)` with types 0 = Signal, 1 = SignalAndIncrementIfEqual,
2 = SignalAndModifyByWaitingCountIfEqual. count <= 0 means ALL.

## Task
Compare OUR functions with Eden's, operation by operation. Report every **behavioural difference** that a game could
observe. Look especially at:
1. **Values written to user memory:** what, when, and whether it is atomic. Compare the
   `SignalAndIncrementIfEqual` and `SignalAndModifyByWaitingCountIfEqual` value computations exactly, and the
   decrement in `DecrementAndWaitIfLessThan`.
2. **Return codes:** InvalidState vs TimedOut vs success, the `timeout == 0` cases, and the order of the checks.
3. **Which waiters get woken:** priority order, `count`, ties (Horizon: lowest priority value first, then FIFO among
   equal priority).
4. **What happens to the waiter list** on timeout/cancel.
5. **Signal before waiting:** the guest writes the value and then calls Signal; can a waiter miss it in our
   implementation?
6. Anything our code does that Eden does not (or vice versa).

## Output format (markdown file, nothing else)
For each difference, one block:
```
### D<n>: <short title>
- ours: <file excerpt line(s) / function> — <what it does>
- horizon (eden): <function> — <what it does>
- observable effect: <what a game would see; could it lose a wakeup / return wrong value / wake wrong thread?>
- severity: HIGH (lost wakeup / wrong value) | MEDIUM | LOW
- fix: <one or two sentences, precise>
```
Put the HIGH ones first. If you are not sure that something is a difference, say "UNSURE" in the severity and why.
Do not invent: quote the exact lines you compare.
