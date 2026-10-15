# W16 — Tradutor Maxwell: instrução ATOM (atômico em memória global), saída GLSL

## Contexto
Um compute shader do jogo usa `ATOM` 18 vezes (ex.: `ed01000001100607` = ATOM.E.ADD.U32). A memória global é o
buffer `gmem_.w[]` (uint de 32 bits); veja em `work/ctx/W16-translate-api.c` como o LDG/STG existente calcula o
endereço (`ga`, `ok`) — siga o mesmo padrão. API: `bits`, `sbits`, `reg`/`R()`, `RZ`, `sp(&c->body, ...)`,
`c->reg_used[]`, `c->info->uses_gmem`, `c->uses_gmem_store`, `maxwell_gmem_base`, `maxwell_gmem_size`, `fail`.

## Entregue
Só UMA função C: `static void emit_atom(Ctx *c, uint64_t w);` (se `!c->glsl`: `fail(c, "atom msl"); return;`).

## Codificação
| campo | bits |
|---|---|
| d (destino: recebe o valor ANTIGO) | 0..7 |
| a (registrador de endereço) | 8..15 |
| b (operando) | 20..27 |
| off (offset com sinal, 20 bits) | 28..47 → `sbits(w, 28, 20)`; se a == RZ, o offset é absoluto sem sinal: `bits(w, 28, 20)` |
| e (endereço de 64 bits: a+1:a) | 48 |
| size | 49..51: 0 U32, 1 S32; qualquer outro → `fail(c, "atom size %d", size)` |
| op | 52..55: 0 ADD, 1 MIN, 2 MAX, 3 INC, 4 DEC, 5 AND, 6 OR, 7 XOR, 8 EXCH; outro → `fail(c, "atom op %d", op)` |

## Endereço (igual ao LDG/STG)
- a == RZ: `ulong(<off>)`
- e: `((ulong(R(a+1)) << 32 | ulong(R(a))) + ulong(<off>))`
- senão: `(ulong(R(a)) + ulong(<off>))`
Abra o bloco: `sp(&c->body, "    { ulong ga = %s - 0x%llxul; bool ok = ga < 0x%llxul; uint old = 0u;\n", addr, base, size);`
Marque `c->info->uses_gmem = true; c->uses_gmem_store = true;`. Índice da palavra: `uint(ga >> 2)`.

## Operação (só se ok; B = R(b))
| op | GLSL dentro de `if (ok) { ... }` |
|---|---|
| ADD | `old = atomicAdd(gmem_.w[wi], B);` |
| MIN U32 | `old = atomicMin(gmem_.w[wi], B);` |
| MAX U32 | `old = atomicMax(gmem_.w[wi], B);` |
| AND / OR / XOR | `atomicAnd` / `atomicOr` / `atomicXor` |
| EXCH | `old = atomicExchange(gmem_.w[wi], B);` |
| MIN/MAX S32, INC, DEC | laço CAS: `uint cur = gmem_.w[wi]; for (;;) { uint nv = <novo>; uint got = atomicCompSwap(gmem_.w[wi], cur, nv); if (got == cur) break; cur = got; } old = cur;` |
`<novo>`: MIN S32 `uint(min(int(cur), int(B)))`; MAX S32 `uint(max(int(cur), int(B)))`; INC `(cur >= B ? 0u : cur + 1u)`; DEC `((cur == 0u || cur > B) ? B : cur - 1u)`.
Declare `uint wi = uint(ga >> 2);` dentro do `if (ok)`.
Depois: se d != RZ: `c->reg_used[d] = 1;` e emita `      r<d> = old;`. Feche o bloco `    }`.

## Aceite (o Claude roda)
1. Compila. 2. Rodada real com `PVR_DIAG_UNKNOWN=1`: nenhum `[unknown-insn] ... ed01...` e nenhum erro de shaderc.
3. Só a função pedida.
