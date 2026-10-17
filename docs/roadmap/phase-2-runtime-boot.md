# Phase 2: Minimal runtime and headless boot

**Goal:** the recompiled game initializes and reaches the main loop **without graphics and without audio** (the NVN and
audio calls become stubs that log and answer "ok").

**In Zelda:** `rt.h` (fixed memory window `0x70_0000_0000`), `loader.c` (NSO + relocs + symbols),
`kernel.c` (handles, threads, mutex/condvar by arbitration, memory, ~50 SVCs), `ipc.c` + `services/`
(20 services), `dispatch.c` (cache + binary search + HLE by name), `main.c` (boot via `nn::init::Start`).

## Tasks
- [x] 2.1 🧠 Memory window (boot run_id=6ea004c868): `GUEST_HI` = 0x80_0000_0000, 48 GiB alias region at
  0x74_0000_0000. The game's `nninitStartup` creates `StandardAllocator(nullptr, 12 GiB)` on top of nn::os's VAMM
  (`GetInfo(16)` != 0 + `MapPhysicalMemory`, which must not zero pages that are already mapped).
- [x] 2.2 🧠 Loader with N modules + rtld HLE (boot run_id=6ea004c868). Bases and build ids come from `pvgame.dll`
  (`layout.py --header`): the host refuses an exefs from another version. Every DT_INIT runs at x3 (after
  `nninitStartup`), because the sdk constructors call the game's `malloc`, which uses main's TLS.
- [ ] 2.3 🤖 Kernel: complete the SVCs the game calls that LAS lacks (the `[svc] UNIMPLEMENTED 0xNN` log
  becomes a card: semantics taken from Switchbrew + reading Eden's `src/core/hle/kernel`).
- [ ] 2.4 🤖 IPC services: one card per new service (list from phase 0). Online (`nifm`, `friends`, `bcat`, `npns`,
  `prepo`, `ssl`, `nsd`...) → **"no network" stub**. Criterion: the game continues without a fatal error.
  Done on 10/14: `pl:u` (shared fonts, card W05, gate pl run_id=c25dcb8f3b), `csrng`, `btm:u` + `IBtmUserCore`.
- [ ] 2.5 🧠 Threads: Pokémon creates many. Validate `ArbitrateLock/Unlock`, `WaitProcessWideKey`,
  `WaitForAddress/SignalToAddress` under load (our own stress test).
  Fixed on 10/14, all inherited from the LAS kernel and different from Horizon:
  (a) on timeout, `WaitProcessWideKeyAtomic` does NOT reacquire the mutex (nn::os/libnx reacquires it);
  (b) `block_current` overwrote a wake that arrived at the same time with a timeout; (c) mutex/condvar consumed the
  `CancelSynchronization` meant for the next `WaitSynchronization`. **Still open:** the boot hangs
  intermittently between 16 and 512 frames, on both versions; the main thread sits in `WaitAny` with 0 handles.
  To investigate, use `PVR_DUMP_THREADS=1`.
  **Solved on 10/14 (qwen, cards with references):**
  - W06 (d): the condvar key is now written BEFORE releasing the mutex. nn::os's `Signal` only calls the kernel if
    key ≠ 0. Reference: Eden `k_condition_variable.cpp` Wait. host v400 run_id=8574b2a012.
  - W07: large NVN commands are split into pieces that fit the game's 1024 B chunks.
    gate cmdbuf_split run_id=dd87dec48f.
  - W08: the memory map became an interval map (split/merge). The old list overflowed with
    "too many regions" with the VAMM. gate regions run_id=4054feb2b8.
- [x] 2.6 🧠 NVN/audio in stub mode: null NVN backend (W03, gate nvn_null run_id=2c624c489d) + null audio SDL
  (W04, gate sdl_null run_id=7bcb24a69b). Boot with frames: base run_id=6c576b773b (`present #64`) and
  v400 run_id=e796f17e2a (`frame_presented`).
- [ ] 2.7 🤖 Structured boot log: sequence of SVCs/IPC; compare with the log of Eden running the same dump.

## Status (10/14, end of day)
On both versions the boot gets to present frames through the null NVN backend: base `present #64` (run_id=6c576b773b) and v400
`frame_presented` (run_id=e796f17e2a). The stopping point varies from 16 to 512 frames (see 2.5).
What it took:
- **Guest setjmp/longjmp.** The recompiled code calls functions as C, and `longjmp` returns into the middle of
  a function. Now `gen.py` generates a checkpoint (CRT `setjmp`) at every `bl setjmp`, and `runtime/setjmp.c`
  does the HLE of `longjmp`. clang's `__builtin_setjmp` does not work on Win64 (it restores the wrong rbp).
- **Compacted `SamplerBuilder`.** It fits in the 0x40 bytes the game reserves on the stack; before, `SetBorderColor` overwrote x29/x30.
- **`GetInfo(20)`** (UserExceptionContextAddress) now returns a valid page.
- **NVN's `HOST()`** now accepts NULL (`BindProgram(cb, NULL)`).

New tools:
- `recomp/disas.py`;
- `recomp/regen_changed.sh` (regenerates and recompiles only the chunks that changed);
- `PVR_GEN_PCLINES=1` (`#line` with the guest PC, for addr2line);
- `PVR_TRACE_HLE=1`;
- `PVR_DUMP_THREADS=1`.

M2 criterion (60 s of `present` without FATAL), measured with `--min-stage frames_60,survived_time_limit --repeat 4`:
- **base v1.0.0: reached, 4 of 4** (`present #1024` in each), run_id=977d5ee1c3;
- **v4.0.0: reached, 6 of 6** (run_id=7adc0390c2). Base reconfirmed with 4 of 4 (run_id=db35401e31).
  Cause of the random failures: `runtime/diag_log.c` (abort log) showed a Lua panic, "attempt to index a nil
  value", in an event coroutine. The root is the address arbiter, which read, modified, and wrote guest memory without
  atomicity, racing with the game's LDXR/STXR. W09 (review done by qwen against Eden) pointed out the problem,
  and W10 (qwen, CAS like Eden's `DecrementIfLessThan`/`UpdateIfEqual`) fixed it.
  Open, low severity: among threads of the same priority, the arbiter wakes the newest first (LIFO);
  Horizon wakes the oldest (FIFO).

**Phase 2 (M2) done on both versions** (v400 run_id=7adc0390c2, base run_id=db35401e31).
Note: until 10/14, `frames_60` passed without any frame when the game merely survived until the time limit. The
`stage_ok` in gates.py fixes this and has a test.

## Exit criterion (M2)
The log shows: modules loaded → `nnMain` → N threads → services opened → loop calling `nvnQueuePresentTexture`
(stub) repeatedly for 60 s without `FATAL`.

## Risks
- Exclusive monitor via compare-and-swap (LAS does it this way): the ABA pattern may show up with more threads; watch for it.
- Services with complex state (`am`/applet, `hid`) need plausible answers so the game does not hang waiting.
