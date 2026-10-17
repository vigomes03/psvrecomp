# W13 — Maxwell Translator: TLD4S Instruction (texture gather, compact form), GLSL Output

## Context
The translator `runtime/nvn/maxwell/translate.c` converts Maxwell shaders to GLSL. The game uses `TLD4S` and today the translation
fails with `unknown instruction df0000c0e3b73a0c` / `df0200c181070f1a`, and the draw is discarded. The API you can use
is in `work/ctx/W13-translate-api.c` (actual snippets from the file): `bits`, `reg`, `RZ`, `tex_slot`,
`write_tex_result`, `glsl_sample` (see how it builds coordinates, `tsize%d` and offsets), `fail`, `c->glsl`, `c->stage`.

## Deliverable
Just ONE C function, nothing else (no includes, no main, no rest of the file):
```c
static void emit_tld4s(Ctx *c, uint64_t w);
```
It will be inserted before `emit_insn` and called when `(w & 0xffc0000000000000) == 0xdf00000000000000`.
If `!c->glsl`: `fail(c, "tld4s msl"); return;`.

## Encoding (bits of the 64-bit word `w`)
| field | bits | meaning |
|---|---|---|
| d0 (`dest_reg_a`) | 0..7 | destination register A |
| a (`src_reg_a`) | 8..15 | source register A |
| b (`src_reg_b`) | 20..27 | source register B |
| d1 (`dest_reg_b`) | 28..35 | destination register B |
| index (`cbuf_offset`) | 36..48 (13 bits) | texture index: `tex_slot(c, index, TEXTYPE_2D, shadow, false)` |
| nodep | 49 | ignore |
| dc | 50 | 1 = depth comparison (shadow texture) |
| aoffi | 51 | 1 = texel offset |
| component | 52..53 | component to gather: 0 R, 1 G, 2 B, 3 A |
| f16 | 55 | 1 = result in packed half precision |

## Operands (registers are uint; `as_type<float>(rN)` gives the float — see `glsl_texs`)
- aoffi=0, dc=0: coords = (float a, float b)
- aoffi=0, dc=1: coords = (float a, float a+1), dref = float b
- aoffi=1, dc=0: coords = (float a, float a+1), offset = b: x = bits 0..5 with sign, y = bits 8..13 with sign
  (`int(rb << 26) >> 26` e `int(rb << 18) >> 26`)
- aoffi=1, dc=1: as above and dref = float b+1
- Offset in GLSL: as in `glsl_sample`, add `vec2(offset) / vec2(tsize<slot>(0).xy)` to the coordinates.

## GLSL Call
- without dc: `textureGather(t<slot>, <vec2>, <component>)` (component is constant int 0..3)
- with dc: `textureGather(t<slot>, <vec2>, <dref>)` (shadow texture: `tex_slot(..., true, false)`)

## Result
The gather returns 4 values (vec4). Use `write_tex_result(c, slot, call, 0xF, d0, d1, true, f16)`:
with `texs=true` it writes to d0, d0+1, d1, d1+1 (or packs into d0/d1 when f16) — exactly the layout of TLD4S.

## Acceptance (the Claude runs)
1. `bash build_host.sh <dir> vulkan` compiles without error with the function inserted.
2. Real run: lines `unknown instruction df00...`/`df02...` disappear from the log and no new `FS translate failed`/error appears for these shaders.
   3. Only the requested function; do not invent fields of `Ctx`/`ShaderInfo` that are not in the context.

