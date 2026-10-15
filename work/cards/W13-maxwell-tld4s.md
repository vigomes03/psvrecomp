# W13 — Tradutor Maxwell: instrução TLD4S (texture gather, forma compacta), saída GLSL

## Contexto
O tradutor `runtime/nvn/maxwell/translate.c` converte shaders Maxwell em GLSL. O jogo usa `TLD4S` e hoje a tradução
falha com `unknown instruction df0000c0e3b73a0c` / `df0200c181070f1a`, e o draw é descartado. A API que você pode usar
está em `work/ctx/W13-translate-api.c` (trechos reais do arquivo): `bits`, `reg`, `RZ`, `tex_slot`,
`write_tex_result`, `glsl_sample` (veja como ele monta coordenadas, `tsize%d` e offsets), `fail`, `c->glsl`, `c->stage`.

## Entregue
Só UMA função C, nada mais (sem includes, sem main, sem o resto do arquivo):
```c
static void emit_tld4s(Ctx *c, uint64_t w);
```
Ela será inserida antes de `emit_insn` e chamada quando `(w & 0xffc0000000000000) == 0xdf00000000000000`.
Se `!c->glsl`: `fail(c, "tld4s msl"); return;`.

## Codificação (bits do word de 64 bits `w`)
| campo | bits | significado |
|---|---|---|
| d0 (`dest_reg_a`) | 0..7 | registrador destino A |
| a (`src_reg_a`) | 8..15 | registrador fonte A |
| b (`src_reg_b`) | 20..27 | registrador fonte B |
| d1 (`dest_reg_b`) | 28..35 | registrador destino B |
| index (`cbuf_offset`) | 36..48 (13 bits) | índice da textura: `tex_slot(c, index, TEXTYPE_2D, shadow, false)` |
| nodep | 49 | ignorar |
| dc | 50 | 1 = comparação de profundidade (textura shadow) |
| aoffi | 51 | 1 = offset de texel |
| component | 52..53 | componente a reunir: 0 R, 1 G, 2 B, 3 A |
| f16 | 55 | 1 = resultado em meia precisão empacotada |

## Operandos (registradores são uint; `as_type<float>(rN)` dá o float — veja `glsl_texs`)
- aoffi=0, dc=0: coords = (float a, float b)
- aoffi=0, dc=1: coords = (float a, float a+1), dref = float b
- aoffi=1, dc=0: coords = (float a, float a+1), offset = b: x = bits 0..5 com sinal, y = bits 8..13 com sinal
  (`int(rb << 26) >> 26` e `int(rb << 18) >> 26`)
- aoffi=1, dc=1: como acima e dref = float b+1
- Offset em GLSL: como em `glsl_sample`, some `vec2(offset) / vec2(tsize<slot>(0).xy)` às coordenadas.

## Chamada GLSL
- sem dc: `textureGather(t<slot>, <vec2>, <component>)` (component é constante int 0..3)
- com dc: `textureGather(t<slot>, <vec2>, <dref>)` (textura shadow: `tex_slot(..., true, false)`)

## Resultado
O gather devolve 4 valores (vec4). Use `write_tex_result(c, slot, call, 0xF, d0, d1, true, f16)`:
com `texs=true` ele grava em d0, d0+1, d1, d1+1 (ou empacota em d0/d1 quando f16) — exatamente o layout do TLD4S.

## Aceite (o Claude roda)
1. `bash build_host.sh <dir> vulkan` compila sem erro com a função inserida.
2. Rodada real: as linhas `unknown instruction df00...`/`df02...` somem do log e nenhum `FS translate failed`/erro de
   shaderc novo aparece para esses shaders.
3. Só a função pedida; sem inventar campos de `Ctx`/`ShaderInfo` que não estão no contexto.
