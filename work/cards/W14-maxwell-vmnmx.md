# W14 — Tradutor Maxwell: instrução VMNMX (video min/max), saída GLSL

## Contexto
Um compute shader do jogo falha com `unknown instruction 3b34086060d70f05` (VMNMX). API disponível em
`work/ctx/W14-translate-api.c` (trechos reais): `bits`, `reg`, `RZ`, `set_reg`, `fail`, `c->glsl`. Registradores
são variáveis GLSL `uint` (ex.: `r12`); `reg(c, n, buf)` devolve o nome ou `0u` para RZ.

## Entregue
Só UMA função C (sem includes, sem o resto do arquivo):
```c
static void emit_vmnmx(Ctx *c, uint64_t w);
```
Se `!c->glsl`: `fail(c, "vmnmx msl"); return;`. O resultado vai para o destino com `set_reg(c, d, expr)`.

## Codificação
| campo | bits |
|---|---|
| d (destino) | 0..7 |
| a (registrador A) | 8..15 |
| b (registrador B, se is_b_reg) | 20..27 |
| b_imm (imediato 16 bits, se !is_b_reg) | 20..35 |
| b_selector | 28..29 |
| b_width | 29..30 |
| c (registrador C) | 39..46 |
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
(sim, os campos selector e width se sobrepõem; copie exatamente.)

## Semântica
1. Se `cc` ou `sat`: `fail(c, "vmnmx cc/sat"); return;`.
2. Operando A = extract(reg a, a_width, a_selector, a_sign).
3. Operando B: se is_b_reg = extract(reg b, b_width, b_selector, b_sign); senão = extract(`<b_imm>u`, width 2, selector 0, b_sign).
4. extract(x, width, sel, signed):
   - width 0 ou 1 (byte): signed → `uint(bitfieldExtract(int(x), SEL*8, 8))`, unsigned → `bitfieldExtract(x, SEL*8, 8)`
   - width 2 (short): o mesmo com SEL*16 e 16 bits
   - width 3 (word): `x`
   (SEL*8 / SEL*16 são números calculados em C e escritos como literal int.)
5. lhs = mx ? max(A, B) : min(A, B), comparação com sinal se b_sign:
   signed → `uint(max(int(A), int(B)))`, unsigned → `max(A, B)`.
6. op: 5 = MIN e 6 = MAX entre lhs e reg c, com sinal se dest_sign (mesma forma do passo 5).
   Qualquer outro op: `fail(c, "vmnmx op %d", op); return;`.
7. `set_reg(c, d, <expressão final>)`. Use buffers de 1024 bytes para as expressões.

## Aceite (o Claude roda)
1. Compila (`build_host.sh <dir> vulkan`).
2. Rodada real: `unknown instruction 3b34...` some do log.
3. Só a função pedida; nada de campos inventados de `Ctx`.
