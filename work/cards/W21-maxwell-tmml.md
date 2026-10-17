# W21 — Maxwell Translator: TMML (mipmap level query), GLSL output

## Context
When the player walks in the open world, the game starts using a pixel shader with the `TMML` instruction
(`df5800812ff70c0a`, opcode `0xDF58` mask `0xFFF8`). The translator does not recognize it (`FS translate failed: unknown
instruction df5800812ff70c0a`), the draw is discarded and the character disappears (only the shadow remains). Reference: Eden
`src/shader_recompiler/frontend/maxwell/translate/impl/texture_mipmap_level.cpp` (local copy, read-only:
`lab/ref/eden/texture_mipmap_level.cpp`). API in `work/ctx/W21-translate-api.c`.

## Delivered
Exactly ONE C function (no includes, no rest of the file):
```c
static void emit_tmml(Ctx *c, uint64_t w);
```
First line: if `!c->glsl`: `fail(c, "tmml msl"); return;`.

## Fields
| field | bits |
|---|---|
| dest (first output register) | 0..7 |
| coord (first coordinate register) | 8..15 |
| type | 28..30 |
| mask (written components) | 31..34 |
| ndv | 35 (ignore) |
| index (texture offset in cbuf) | 36..48 (13 bits) |
| nodep | 49 (ignore) |

If `mask & 0xC` != 0: `fail(c, "tmml mask %x", mask); return;` (Eden also does not implement components 2 and 3).

## type → TEXTYPE, array and GLSL coordinate
`C(k)` = `uintBitsToFloat(R(coord + k))`. If `coord` == RZ (255): use `0.0f` instead of each `C(k)`.
| type | TEXTYPE | array | coordinate (array index DOES NOT enter) |
|---|---|---|---|
| 0 | TEXTYPE_1D | false | `C(0)` |
| 1 | TEXTYPE_1D_ARRAY | true | `C(1)` |
| 2 | TEXTYPE_2D | false | `vec2(C(0), C(1))` |
| 3 | TEXTYPE_2D_ARRAY | true | `vec2(C(1), C(2))` |
| 4 | TEXTYPE_3D | false | `vec3(C(0), C(1), C(2))` |
| 5 | — | — | `fail(c, "tmml 3d array"); return;` |
| 6 | TEXTYPE_CUBE | false | `vec3(C(0), C(1), C(2))` |
| 7 | TEXTYPE_CUBE_ARRAY | true | `vec3(C(1), C(2), C(3))` |

## Texture
```c
uint32_t index = (uint32_t)bits(w, 36, 13);
bool shadow = c->tex_slot[index] ? c->info->tex[c->tex_slot[index] - 1].shadow : false;  // maintains previous usage
int slot = tex_slot(c, index, textype, shadow, array);
```

## Emitted GLSL
```
    { vec2 lod = textureQueryLod(t<slot>, <coordinate>);
      r<d> = uint(lod.x) << 8u;      // only mask bit 0
      r<d+1> = uint(lod.y) << 8u;    // only mask bit 1 (goes to the NEXT free register)
    }
```
The output registers are consecutive starting from `dest`, one per bit set in the mask (as in TXQ: the
component 1 goes to `dest` if bit 0 is off). For each register written: `c->reg_used[r] = 1`.
If `dest` == RZ: calculate but do not write anything (no `r255`).

## Example (the actual instruction)
`w = 0xdf5800812ff70c0a`: dest = 10, coord = 12, type = 2 (2D), mask = 2 (only component 1), index = 0x8
(checked by script). Expected output (slot 0 if it's the first texture):
```
    { vec2 lod = textureQueryLod(t0, vec2(uintBitsToFloat(r12), uintBitsToFloat(r13)));
      r10 = uint(lod.y) << 8u;
    }
```
(component 1 goes to r10 because bit 0 of the mask is off)

## Do not do
- Nothing with `TMML.B` (bindless, `0xDF60`): it is not used.
- Do not touch the rest of the file; do not declare the sampler (the translator declares `t<slot>` later).
