# W07 — NVN: split large commands across command-memory chunks (`runtime/nvn/cmdbuf.c`)

## Bug (found by Claude with evidence; 14/10)
Some v4.0.0 boots die with:
`FATAL: nvn: out of command memory (need 1568; chunk 76ea495000 size 1024 used 0, callback 7002652b50)`.

Our recorder (context `cmdbuf.c`) writes each NVN command as ONE `CmdRec`:
- the header is 80 bytes (`op`, `size`, `x[7]`, `f[4]`), followed by the copied data (`extra`);
- the record must fit in the current guest command-memory chunk, with `JUMP_RESERVE` left over.

When it doesn't fit, `rec()` calls the game's memory callback, which hands over a **1024-byte chunk**. The real NVN
encodes commands in small GPU methods and never needs one contiguous block of 1.5 KB, so the game never gives more.
`nvnCommandBufferUpdateUniformBuffer` with 1488 bytes of data needs 1568 bytes. After two callbacks, `rec()` gives
up with FATAL.

## Task: split, without changing the record format
Commands whose data is a list of independent pieces become **several consecutive records of the same op**. The
data goes in order, so a reader that executes the records one by one gets exactly the same result. Nothing on the
reader side changes.

Output: ONE C file containing ONLY these definitions; it is spliced into `cmdbuf.c` with
`tools/workers/splice_c_function.py` (new functions go before the first replaced one):
1. NEW `static void record_copy_split(Cpu *c, uint32_t op, int count_arg, int ptr_arg, uint32_t unit,
   uint32_t max_units, int offset_arg)`.
   - Snapshot the call ONCE: `Snap s = snap(c);`, before any `rec`, because `rec` may call the guest callback.
   - Total units = `s.x[count_arg]`; data pointer = `s.x[ptr_arg]`; each unit is `unit` bytes.
   - Loop over pieces of at most `max_units` units. For each piece:
     - make `Snap p = s;` and set `p.x[count_arg]` = units in this piece;
     - set `p.x[ptr_arg] = s.x[ptr_arg] + done * unit` (keep the pointer consistent for the record);
     - if `offset_arg >= 0`, set `p.x[offset_arg] = s.x[offset_arg] + done * unit`;
     - `CmdRec *r = record(c, op, n * unit, &p);`
     - `memcpy(r->extra, (const uint8_t *)(uintptr_t)s.x[ptr_arg] + done * unit, n * unit)`.
   - Total 0 → record ONE record with 0 bytes, as `record_copy` does today (keeps the behavior).
   - Do not change `c->x[]` (the test checks that the caller's x0 and x5 come back intact).
2. REPLACE `NVN(nvnCommandBufferUpdateUniformBuffer)`. NVN signature:
   `(cmdBuf x0, buffer x1, bufferSize x2, updateOffset x3, updateSize x4, data x5)`. Use
   `record_copy_split(c, CMD_UPDATE_UNIFORM_BUFFER, 4, 5, 1, PIECE_BYTES, 3)` (unit = 1 byte, offset in x3).
3. REPLACE `NVN(nvnCommandBufferCallCommands)` and `NVN(nvnCommandBufferCopyCommands)`. Signature:
   `(cmdBuf x0, numCommands x1, handles x2)`. Use `record_copy_split(c, CMD_CALL, 1, 2, 8, PIECE_BYTES / 8, -1)`.
4. Put `#define PIECE_BYTES 512u` ABOVE `record_copy_split`, in the same file you deliver: 80 + 512 + `JUMP_RESERVE`
   (88) = 680 ≤ 1024.

Index reminder: `Snap.x[i]` is the call's `x[i]` (`x0`..`x7`). `record()` copies `s->x + 1` into `r->x`, so in the
record `r->x[0]` = call x1, and so on. Do not change `record`, `rec`, `snap` or `record_copy`.

## Acceptance (Claude runs it; do not claim it yourself)
`python tools/verify/gates.py run cmdbuf_split`. It compiles `recomp/test_cmdbuf_split.c` (context) with
`-Wall -Werror` against the real `cmdbuf.c` and runs it. The test:
- feeds a 1488-byte UpdateUniformBuffer, a 200-handle CallCommands and a small 64-byte update;
- uses a callback that hands out 1024-byte chunks;
- walks the list (following `CMD_JUMP`) and checks that the pieces have the right offsets, are in order, rebuild
  the data byte for byte and that every record fits in a chunk. It must print `W07 PASS`.
