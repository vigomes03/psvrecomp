# W17 — Maxwell Translator: SUST and SURED (storage images), GLSL output

## Context
Two pixel shaders from the game (full-screen passes at 480x270) use `SUST` (`eb20010600f70004`) and `SURED`
(`eb50008602070a00`); without them the 3D scene turns black. The infrastructure already exists (Claude did it): `img_slot(...)` registers the
image and returns the index `i`; in GLSL it is called `img<i>` and is `uimage1D/uimage2D/...` with format `r32ui`.
API in `work/ctx/W17-translate-api.c`: `bits`, `reg`/`R()`, `RZ`, `sp(&c->body, ...)`, `fail`, `img_slot`, `c->glsl`.

## Deliverables
Exactly TWO C functions (no includes, no rest of the file):
```c
static void emit_sust(Ctx *c, uint64_t w);
static void emit_sured(Ctx *c, uint64_t w);
```
In both: if `!c->glsl`: `fail(c, "surface msl"); return;`.

## Common Fields (SUST and SURED)
| field | bits |
|---|---|
| r0 (data in SUST / value in SURED) | 0..7 |
| rc (first coordinate register) | 8..15 |
| type | 33..35 |
| bound_offset | 36..48 (13 bits) |
| bindless_reg (handle) | 39..46 |
| clamp | 49..50 → if != 0: `fail(c, "surface clamp")` |
| is_bound | 51 |

`type` Maxwell → TEXTYPE and GLSL coordinate (`C(k)` = register rc+k):
| type | TEXTYPE | coordinate |
|---|---|---|
| 0 | TEXTYPE_1D | `int(C0)` |
| 1 | — | `fail(c, "surface buffer")` |
| 2 | TEXTYPE_1D_ARRAY | `ivec2(int(C0), int(C1 & 0xFFFFu))` |
| 3 | TEXTYPE_2D | `ivec2(int(C0), int(C1))` |
| 4 | TEXTYPE_2D_ARRAY | `ivec3(int(C0), int(C1), int(C2 & 0xFFFFu))` |
| 5 | TEXTYPE_3D | `ivec3(int(C0), int(C1), int(C2))` |
| 6, 7 | — | `fail(c, "surface type %d")` |

Image: `int i = img_slot(c, bits(w, 51, 1), (uint32_t)bits(w, 36, 13), (int)bits(w, 39, 8), textype);`
(call AFTER validating clamp/type). Registers: use `R(n)` (returns "r5" or "0u" for RZ). Do not call
`R(rc + k)` with rc == RZ (use "0u").

## SUST
- d (typed) = bit 52. If d == 1: size = bits 20..22; number of registers: size <= 4 → 1, 5 → 2, 6 → 4, 7 → `fail`.
  If d == 0 (.P): swizzle = bits 20..23; if != 0xF → `fail(c, "sust mask %x", swz)`; uses 4 registers.
- Value: `uvec4(R(r0), R(r0+1) ou 0u, R(r0+2) ou 0u, R(r0+3) ou 0u)` according to the number of registers.
- Emit: `sp(&c->body, "    imageStore(img%d, %s, %s);\n", i, coord, value);`

## SURED (atomic reduction, no result)
- size = bits 20..22: 0 (U32) or 1 (S32); otherwise → `fail(c, "sured size %d")`.
- op = bits 24..26: 0 ADD, 1 MIN, 2 MAX, 3 INC, 4 DEC, 5 AND, 6 OR, 7 XOR.
- GLSL (V = R(r0)):
  | op | U32 | S32 |
  |---|---|---|
  | ADD | `imageAtomicAdd(img<i>, COORD, V)` | same |
  | MIN | `imageAtomicMin(img<i>, COORD, V)` | `fail(c, "sured smin")` |
  | MAX | `imageAtomicMax(img<i>, COORD, V)` | `fail(c, "sured smax")` |
  | AND / OR / XOR | `imageAtomicAnd/Or/Xor(img<i>, COORD, V)` | same |
  | INC / DEC | `fail(c, "sured inc/dec")` | same |
- Emit: `sp(&c->body, "    %s;\n", chamada);`

## Acceptance (Claude runs)
1. Compiles. 2. Runs with `PVR_DIAG_UNKNOWN=1`: no `[unknown-insn]` from `eb20...`/`eb50...`, no shaderc error,
`prog_failed` drops to 0. 3. Only the two functions.
