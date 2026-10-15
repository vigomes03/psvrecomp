# W17 — Tradutor Maxwell: SUST e SURED (storage images), saída GLSL

## Contexto
Dois shaders de pixel do jogo (passes de tela cheia em 480x270) usam `SUST` (`eb20010600f70004`) e `SURED`
(`eb50008602070a00`); sem eles a cena 3D fica preta. A infraestrutura já existe (o Claude fez): `img_slot(...)` registra a
imagem e devolve o índice `i`; no GLSL ela se chama `img<i>` e é `uimage1D/uimage2D/...` com formato `r32ui`.
API em `work/ctx/W17-translate-api.c`: `bits`, `reg`/`R()`, `RZ`, `sp(&c->body, ...)`, `fail`, `img_slot`, `c->glsl`.

## Entregue
Exatamente DUAS funções C (sem includes, sem o resto do arquivo):
```c
static void emit_sust(Ctx *c, uint64_t w);
static void emit_sured(Ctx *c, uint64_t w);
```
Nas duas: se `!c->glsl`: `fail(c, "surface msl"); return;`.

## Campos comuns (SUST e SURED)
| campo | bits |
|---|---|
| r0 (dados no SUST / valor no SURED) | 0..7 |
| rc (primeiro registrador de coordenadas) | 8..15 |
| type | 33..35 |
| bound_offset | 36..48 (13 bits) |
| bindless_reg (handle) | 39..46 |
| clamp | 49..50 → se != 0: `fail(c, "surface clamp")` |
| is_bound | 51 |

`type` Maxwell → TEXTYPE e coordenada GLSL (`C(k)` = registrador rc+k):
| type | TEXTYPE | coordenada |
|---|---|---|
| 0 | TEXTYPE_1D | `int(C0)` |
| 1 | — | `fail(c, "surface buffer")` |
| 2 | TEXTYPE_1D_ARRAY | `ivec2(int(C0), int(C1 & 0xFFFFu))` |
| 3 | TEXTYPE_2D | `ivec2(int(C0), int(C1))` |
| 4 | TEXTYPE_2D_ARRAY | `ivec3(int(C0), int(C1), int(C2 & 0xFFFFu))` |
| 5 | TEXTYPE_3D | `ivec3(int(C0), int(C1), int(C2))` |
| 6, 7 | — | `fail(c, "surface type %d")` |

Imagem: `int i = img_slot(c, bits(w, 51, 1), (uint32_t)bits(w, 36, 13), (int)bits(w, 39, 8), textype);`
(chame DEPOIS de validar clamp/type). Registradores: use `R(n)` (devolve "r5" ou "0u" para RZ). Não chame
`R(rc + k)` com rc == RZ (use "0u").

## SUST
- d (typed) = bit 52. Se d == 1: size = bits 20..22; nº de registradores: size <= 4 → 1, 5 → 2, 6 → 4, 7 → `fail`.
  Se d == 0 (.P): swizzle = bits 20..23; se != 0xF → `fail(c, "sust mask %x", swz)`; usa 4 registradores.
- Valor: `uvec4(R(r0), R(r0+1) ou 0u, R(r0+2) ou 0u, R(r0+3) ou 0u)` conforme o nº de registradores.
- Emita: `sp(&c->body, "    imageStore(img%d, %s, %s);\n", i, coord, value);`

## SURED (redução atômica, sem resultado)
- size = bits 20..22: 0 (U32) ou 1 (S32); outro → `fail(c, "sured size %d")`.
- op = bits 24..26: 0 ADD, 1 MIN, 2 MAX, 3 INC, 4 DEC, 5 AND, 6 OR, 7 XOR.
- GLSL (V = R(r0)):
  | op | U32 | S32 |
  |---|---|---|
  | ADD | `imageAtomicAdd(img<i>, COORD, V)` | igual |
  | MIN | `imageAtomicMin(img<i>, COORD, V)` | `fail(c, "sured smin")` |
  | MAX | `imageAtomicMax(img<i>, COORD, V)` | `fail(c, "sured smax")` |
  | AND / OR / XOR | `imageAtomicAnd/Or/Xor(img<i>, COORD, V)` | igual |
  | INC / DEC | `fail(c, "sured inc/dec")` | idem |
- Emita: `sp(&c->body, "    %s;\n", chamada);`

## Aceite (o Claude roda)
1. Compila. 2. Rodada com `PVR_DIAG_UNKNOWN=1`: sem `[unknown-insn]` de `eb20...`/`eb50...`, sem erro de shaderc,
`prog_failed` cai para 0. 3. Só as duas funções.
