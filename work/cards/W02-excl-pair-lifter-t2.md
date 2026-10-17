# W02: Lifter function for LDXP/LDAXP/STXP/STLXP (64 bits)

## Objective
Write `recomp/excl_pair.py` with a function `lift_excl_pair(w, pc)` that translates the AArch64 instruction `w`
(32-bit word) into a C line, using the helpers from `runtime/excl_pair.h`.

## API that ALREADY EXISTS (import from `lifter`; do not reimplement)
```python
from lifter import Insn, Unsupported, bits, X, XS, set_reg
bits(w, lo, n)      # field of n bits starting at bit lo
X(r)                # C expression of register Xr as value; r == 31 -> '0ull' (XZR)
XS(r)               # same, but r == 31 -> 'c->sp' (use for base address Rn)
set_reg(sf, r, e)   # C instruction that writes e in Xr (sf=1: 64 bits); r == 31 -> discard
Insn('op', code)    # return: common instruction with the C code
raise Unsupported(msg)
```
C helpers available in the generated code:
`ldxp64(c, a, &lo, &hi)`, `ldaxp64(c, a, &lo, &hi)`, `stxp64(c, a, lo, hi)` → uint32_t (0 = ok), `stlxp64(...)`.

## Encoding (only the 64-bit case; the rest raises Unsupported)
| field | bits | value |
|---|---|---|
| sz | 30 | 1 = 64 bits (if 0: `raise Unsupported('excl pair 32')`) |
| L | 22 | 1 = load (LDXP/LDAXP), 0 = store (STXP/STLXP) |
| o2 | 23 | must be 0 (if 1: `raise Unsupported('cas pair')`) |
| o1 | 21 | is 1 (that's why we're here) |
| Rs | 20:16 | store status register (W) |
| o0 | 15 | 1 = acquire (load) / release (store) |
| Rt2 | 14:10 | second register |
| Rn | 9:5 | base (31 = SP) |
| Rt | 4:0 | first register |

## Expected output (C inside ONE brace block for the local variables)
- Load: `{ uint64_t lo, hi; ldxp64(c, <XS(rn)>, &lo, &hi); <set_reg(1, rt, 'lo')> <set_reg(1, rt2, 'hi')> }`
  (with `o0 == 1` use `ldaxp64`)
- Store: `{ uint32_t st = stxp64(c, <XS(rn)>, <X(rt)>, <X(rt2)>); <set_reg(0, rs, 'st')> }`
  (with `o0 == 1` use `stlxp64`)

## Case table (acceptance: the generated code must be identical to this, ignoring whitespace)
| word | instruction | expected C |
|---|---|---|
| `0xc87f2401` | `ldxp x1, x9, [x0]` | `{ uint64_t lo, hi; ldxp64(c, c->x[0], &lo, &hi); c->x[1] = (uint64_t)(lo); c->x[9] = (uint64_t)(hi); }` |
| `0xc87fa7e1` | `ldaxp x1, x9, [sp]` | `{ uint64_t lo, hi; ldaxp64(c, c->sp, &lo, &hi); c->x[1] = (uint64_t)(lo); c->x[9] = (uint64_t)(hi); }` |
| `0xc8222401` | `stxp w2, x1, x9, [x0]` | `{ uint32_t st = stxp64(c, c->x[0], c->x[1], c->x[9]); c->x[2] = (uint32_t)(st); }` |
| `0xc822ffe1` | `stlxp w2, x1, xzr, [sp]` | `{ uint32_t st = stlxp64(c, c->sp, c->x[1], 0ull); c->x[2] = (uint32_t)(st); }` |
| `0x887f2401` | `ldxp w1, w9, [x0]` | `raise Unsupported` |

Answer with ONE ```python block with the complete `excl_pair.py` file.

## ATTEMPT 2: attempt 1 was REJECTED
A single, systematic error: `bits(w, lo, n)` takes the **LOWEST** bit of the field. You passed the highest one.
The correct fields are exactly:
```python
rs  = bits(w, 16, 5)   # Rs  = bits 20..16  (you used bits(w, 20, 5): WRONG)
rt2 = bits(w, 10, 5)   # Rt2 = bits 14..10  (you used bits(w, 14, 5): WRONG)
rn  = bits(w, 5, 5)    # Rn  = bits 9..5    (you used bits(w, 9, 5): WRONG)
rt  = bits(w, 0, 5)    # Rt  = bits 4..0    (you used bits(w, 4, 5): WRONG)
```
Result of attempt 1 for `0xc87f2401` (ldxp x1, x9, [x0]): it produced `ldxp64(c, c->x[18], ...); c->x[0] = lo; c->x[28] = hi`;
the correct one is `ldxp64(c, c->x[0], ...); c->x[1] = lo; c->x[9] = hi`. The rest of the file was right; keep it.
