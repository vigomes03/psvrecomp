# W02: função do lifter para LDXP/LDAXP/STXP/STLXP (64 bits)

## Objetivo
Escrever `recomp/excl_pair.py` com UMA função `lift_excl_pair(w, pc)` que traduz a instrução AArch64 `w`
(palavra de 32 bits) para uma linha de C, usando os helpers de `runtime/excl_pair.h`.

## API que JÁ EXISTE (importe de `lifter`; não reimplemente)
```python
from lifter import Insn, Unsupported, bits, X, XS, set_reg
bits(w, lo, n)      # campo de n bits a partir do bit lo
X(r)                # expressão C do registrador Xr como valor; r == 31 -> '0ull' (XZR)
XS(r)               # igual, mas r == 31 -> 'c->sp' (use para o endereço base Rn)
set_reg(sf, r, e)   # instrução C que grava e em Xr (sf=1: 64 bits); r == 31 -> descarta
Insn('op', code)    # retorno: instrução comum com o código C
raise Unsupported(msg)
```
Helpers C disponíveis no código gerado:
`ldxp64(c, a, &lo, &hi)`, `ldaxp64(c, a, &lo, &hi)`, `stxp64(c, a, lo, hi)` → uint32_t (0 = ok), `stlxp64(...)`.

## Codificação (só o caso 64 bits; o resto levanta Unsupported)
| campo | bits | valor |
|---|---|---|
| sz | 30 | 1 = 64 bits (se 0: `raise Unsupported('excl pair 32')`) |
| L | 22 | 1 = load (LDXP/LDAXP), 0 = store (STXP/STLXP) |
| o2 | 23 | deve ser 0 (se 1: `raise Unsupported('cas pair')`) |
| o1 | 21 | é 1 (é por isso que caímos aqui) |
| Rs | 20:16 | registrador de status do store (W) |
| o0 | 15 | 1 = acquire (load) / release (store) |
| Rt2 | 14:10 | segundo registrador |
| Rn | 9:5 | base (31 = SP) |
| Rt | 4:0 | primeiro registrador |

## Saída esperada (C dentro de UMA chave para as variáveis locais)
- Load: `{ uint64_t lo, hi; ldxp64(c, <XS(rn)>, &lo, &hi); <set_reg(1, rt, 'lo')> <set_reg(1, rt2, 'hi')> }`
  (com `o0 == 1` use `ldaxp64`)
- Store: `{ uint32_t st = stxp64(c, <XS(rn)>, <X(rt)>, <X(rt2)>); <set_reg(0, rs, 'st')> }`
  (com `o0 == 1` use `stlxp64`)

## Tabela de casos (aceite: o código gerado deve ser idêntico a isto, ignorando espaços)
| palavra | instrução | C esperado |
|---|---|---|
| `0xc87f2401` | `ldxp x1, x9, [x0]` | `{ uint64_t lo, hi; ldxp64(c, c->x[0], &lo, &hi); c->x[1] = (uint64_t)(lo); c->x[9] = (uint64_t)(hi); }` |
| `0xc87fa7e1` | `ldaxp x1, x9, [sp]` | `{ uint64_t lo, hi; ldaxp64(c, c->sp, &lo, &hi); c->x[1] = (uint64_t)(lo); c->x[9] = (uint64_t)(hi); }` |
| `0xc8222401` | `stxp w2, x1, x9, [x0]` | `{ uint32_t st = stxp64(c, c->x[0], c->x[1], c->x[9]); c->x[2] = (uint32_t)(st); }` |
| `0xc822ffe1` | `stlxp w2, x1, xzr, [sp]` | `{ uint32_t st = stlxp64(c, c->sp, c->x[1], 0ull); c->x[2] = (uint32_t)(st); }` |
| `0x887f2401` | `ldxp w1, w9, [x0]` | `raise Unsupported` |

Responda com UM bloco ```python com o arquivo completo `excl_pair.py`.
