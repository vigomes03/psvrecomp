# W16 — Maxwell Translator: ATOM instruction (atomic in global memory), GLSL output

## Context
A compute shader from the game uses `ATOM` 18 times (e.g., `ed01000001100607` = ATOM.E.ADD.U32). The global memory is the
buffer `gmem_.w[]` (32-bit uint); see in `work/ctx/W16-translate-api.c` how the existing LDG/STG calculates the
address (`ga`, `ok`) — follow the same pattern. API: `bits`, `sbits`, `reg`/`R()`, `RZ`, `sp(&c->body, ...)`,
`c->reg_used[]`, `c->info->uses_gmem`, `c->uses_gmem_store`, `maxwell_gmem_base`, `maxwell_gmem_size`, `fail`.

## Deliverable
Only ONE C function: `static void emit_atom(Ctx *c, uint64_t w);` (if `!c->glsl`: `fail(c, "atom msl"); return;`).

## Encoding
| field | bits |
|---|---|
| d (destination: receives the OLD value) | 0..7 |
| a (address register) | 8..15 |
| b (operand) | 20..27 |
| off (signed offset, 20 bits) | 28..47 → `sbits(w, 28, 20)`; if a == RZ, the offset is unsigned absolute: `bits(w, 28, 20)` |
| e (64-bit address: a+1:a) | 48 |
| size | 49..51: 0 U32, 1 S32; any other → `fail(c, "atom size %d", size)` |
| op | 52..55: 0 ADD, 1 MIN, 2 MAX, 3 INC, 4 DEC, 5 AND, 6 OR, 7 XOR, 8 EXCH; other → `fail(c, "atom op %d", op)` |

## Address (same as LDG/STG)
- a == RZ: `ulong(<off>)`
- e: `((ulong(R(a+1)) << 32 | ulong(R(a))) + ulong(<off>))`
- otherwise: `(ulong(R(a)) + ulong(<off>))`
Open the block: `sp(&c->body, "    { ulong ga = %s - 0x%llxul; bool ok = ga < 0x%llxul; uint old = 0u;\n", addr, base, size);`
Mark `c->info->uses_gmem = true; c->uses_gmem_store = true;`. Word index: `uint(ga >> 2)`.

## Operation (only if ok; B = R(b))
| op | GLSL inside `if (ok) { ... }` |
|---|---|
| ADD | `old = atomicAdd(gmem_.w[wi], B);` |
| MIN U32 | `old = atomicMin(gmem_.w[wi], B);` |
| MAX U32 | `old = atomicMax(gmem_.w[wi], B);` |
| AND / OR / XOR | `atomicAnd` / `atomicOr` / `atomicXor` |
| EXCH | `old = atomicExchange(gmem_.w[wi], B);` |
| MIN/MAX S32, INC, DEC | CAS loop: `uint cur = gmem_.w[wi]; for (;;) { uint nv = <novo>; uint got = atomicCompSwap(gmem_.w[wi], cur, nv); if (got == cur) break; cur = got; } old = cur;` |
`<novo>`: MIN S32 `uint(min(int(cur), int(B)))`; MAX S32 `uint(max(int(cur), int(B)))`; INC `(cur >= B ? 0u : cur + 1u)`; DEC `((cur == 0u || cur > B) ? B : cur - 1u)`.
Declare `uint wi = uint(ga >> 2);` inside the `if (ok)`.
After: if d != RZ: `c->reg_used[d] = 1;` and emit `      r<d> = old;`. Close the block `    }`.

## Accept (Claude runs)
1. Compile. 2. Real run with `PVR_DIAG_UNKNOWN=1`: no `[unknown-insn] ... ed01...` and no shaderc errors.
3. Only the requested function.
