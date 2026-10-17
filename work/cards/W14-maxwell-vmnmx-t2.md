# W14 — Maxwell Translator: VMNMX Instruction (video min/max), GLSL Output

## Context
A compute shader from the game fails with `unknown instruction 3b34086060d70f05` (VMNMX). Available API in
`work/ctx/W14-translate-api.c` (actual snippets): `bits`, `reg`, `RZ`, `set_reg`, `fail`, `c->glsl`. Registers
are GLSL `uint` variables (e.g., `r12`); `reg(c, n, buf)` returns the name or `0u` for RZ.

## Deliverable
Only ONE C function (no includes, no rest of the file):
```c
static void emit_vmnmx(Ctx *c, uint64_t w);
```
If `!c->glsl`: `fail(c, "vmnmx msl"); return;`. The result goes to the destination with `set_reg(c, d, expr)`.

## Encoding
| field | bits |
|---|---|
| d (destination) | 0..7 |
| a (register A) | 8..15 |
| b (register B, if is_b_reg) | 20..27 |
| b_imm (16-bit immediate, if !is_b_reg) | 20..35 |
| b_selector | 28..29 |
| b_width | 29..30 |
| c (register C) | 39..46 |
| a_selector | 36..37 |
| a_width | 37..38 |
| cc | 47 |
| a_sign | 48 |
| b_sign | 49 |
| is_b_reg | 50 |
| op | 51..53 |
| dest_sign | 54 |
| sat | 55 |
| mx | 56 |
(yes, the selector and width fields overlap; copy exactly.)

## Semantics
1. If `cc` or `sat`: `fail(c, "vmnmx cc/sat"); return;`.
2. Operand A = extract(reg a, a_width, a_selector, a_sign).
3. Operand B: if is_b_reg = extract(reg b, b_width, b_selector, b_sign); else = extract(`<b_imm>u`, width 2, selector 0, b_sign).
4. extract(x, width, sel, signed):
   - width 0 or 1 (byte): signed → `uint(bitfieldExtract(int(x), SEL*8, 8))`, unsigned → `bitfieldExtract(x, SEL*8, 8)`
   - width 2 (short): same with SEL*16 and 16 bits
   - width 3 (word): `x`
   (SEL*8 / SEL*16 are numbers calculated in C and written as literal int.)
5. lhs = mx ? max(A, B) : min(A, B), comparison with sign if b_sign:
   signed → `uint(max(int(A), int(B)))`, unsigned → `max(A, B)`.
6. op: 5 = MIN and 6 = MAX between lhs and reg c, with sign if dest_sign (same form as step 5).
   Any other op: `fail(c, "vmnmx op %d", op); return;`.
7. `set_reg(c, d, <final expression>)`. Use buffers of 1024 bytes for the expressions.

## Acceptance (Claude runs)
1. Compile (`build_host.sh <dir> vulkan`).
2. Real run: `unknown instruction 3b34...` some from log.
3. Only the requested function; no invented fields of `Ctx`.


## ATTEMPT 2 — ATTEMPT 1 WAS REJECTED
Errors (fix all):
1. `int c = bits(w, 39, 8);` hides the parameter `Ctx *c` and breaks `R()`, `fail()`, `set_reg()`. Rename register C to `rc`.
2. DO NOT use `F(...)`: F reinterprets as float (`as_type<float>`). The values here are uint; use the strings directly.
3. Each expression needs its OWN buffer: `char ea[256], eb[256], el[600], ef[1024];` (A, B, lhs, final).
   Reusing a single `buf` makes the pointers point to the same text.
4. Width 3 (word): the operand is the entire register, without bitfieldExtract.
5. Immediate: width 16 and selector 0 always: `bitfieldExtract(<imm>u, 0, 16)` (signed: `uint(bitfieldExtract(int(<imm>u), 0, 16))`).
Suggested structure: an auxiliary function `static void vmnmx_extract(char *out, const char *x, int width, int sel, bool sgn)`
NOT allowed (only one function); do the extraction inline twice, with the buffers ea/eb.
