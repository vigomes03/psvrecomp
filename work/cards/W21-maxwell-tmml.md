# W21 — Tradutor Maxwell: TMML (consulta de nível de mipmap), saída GLSL

## Contexto
Quando o jogador anda no mundo aberto, o jogo passa a usar um shader de pixel com a instrução `TMML`
(`df5800812ff70c0a`, opcode `0xDF58` máscara `0xFFF8`). O tradutor não a conhece (`FS translate failed: unknown
instruction df5800812ff70c0a`), o draw é descartado e o personagem some (só a sombra fica). Referência: Eden
`src/shader_recompiler/frontend/maxwell/translate/impl/texture_mipmap_level.cpp` (cópia local, só leitura:
`lab/ref/eden/texture_mipmap_level.cpp`). API em `work/ctx/W21-translate-api.c`.

## Entregue
Exatamente UMA função C (sem includes, sem o resto do arquivo):
```c
static void emit_tmml(Ctx *c, uint64_t w);
```
Primeira linha: se `!c->glsl`: `fail(c, "tmml msl"); return;`.

## Campos
| campo | bits |
|---|---|
| dest (primeiro registrador de saída) | 0..7 |
| coord (primeiro registrador de coordenadas) | 8..15 |
| type | 28..30 |
| mask (componentes escritos) | 31..34 |
| ndv | 35 (ignorar) |
| index (offset da textura no cbuf) | 36..48 (13 bits) |
| nodep | 49 (ignorar) |

Se `mask & 0xC` != 0: `fail(c, "tmml mask %x", mask); return;` (o Eden também não implementa os componentes 2 e 3).

## type → TEXTYPE, array e coordenada GLSL
`C(k)` = `uintBitsToFloat(R(coord + k))`. Se `coord` == RZ (255): use `0.0f` no lugar de cada `C(k)`.
| type | TEXTYPE | array | coordenada (o índice de array NÃO entra) |
|---|---|---|---|
| 0 | TEXTYPE_1D | false | `C(0)` |
| 1 | TEXTYPE_1D_ARRAY | true | `C(1)` |
| 2 | TEXTYPE_2D | false | `vec2(C(0), C(1))` |
| 3 | TEXTYPE_2D_ARRAY | true | `vec2(C(1), C(2))` |
| 4 | TEXTYPE_3D | false | `vec3(C(0), C(1), C(2))` |
| 5 | — | — | `fail(c, "tmml 3d array"); return;` |
| 6 | TEXTYPE_CUBE | false | `vec3(C(0), C(1), C(2))` |
| 7 | TEXTYPE_CUBE_ARRAY | true | `vec3(C(1), C(2), C(3))` |

## Textura
```c
uint32_t index = (uint32_t)bits(w, 36, 13);
bool shadow = c->tex_slot[index] ? c->info->tex[c->tex_slot[index] - 1].shadow : false;  // mantém o uso anterior
int slot = tex_slot(c, index, textype, shadow, array);
```

## GLSL emitido
```
    { vec2 lod = textureQueryLod(t<slot>, <coordenada>);
      r<d> = uint(lod.x) << 8u;      // só se mask bit 0
      r<d+1> = uint(lod.y) << 8u;    // só se mask bit 1 (vai para o PRÓXIMO registrador livre)
    }
```
Os registradores de saída são consecutivos a partir de `dest`, um por bit ligado da máscara (como no TXQ: o
componente 1 vai para `dest` se o bit 0 estiver desligado). Para cada registrador escrito: `c->reg_used[r] = 1`.
Se `dest` == RZ: calcule mas não escreva nada (sem `r255`).

## Exemplo (a instrução real)
`w = 0xdf5800812ff70c0a`: dest = 10, coord = 12, type = 2 (2D), mask = 2 (só o componente 1), index = 0x8
(conferido por script). Saída esperada (slot 0 se for a primeira textura):
```
    { vec2 lod = textureQueryLod(t0, vec2(uintBitsToFloat(r12), uintBitsToFloat(r13)));
      r10 = uint(lod.y) << 8u;
    }
```
(o componente 1 vai para r10 porque o bit 0 da máscara está desligado)

## Não fazer
- Nada de `TMML.B` (bindless, `0xDF60`): não é usado.
- Não mexer no resto do arquivo; não declarar o sampler (o tradutor declara `t<slot>` depois).
