// Excerpts of Pokemon Decompile/runtime/nvn/maxwell/translate.c (registers are GLSL uint r0..r254)
#define RZ 255
enum { TEXTYPE_1D, TEXTYPE_2D, TEXTYPE_3D, TEXTYPE_CUBE, TEXTYPE_2D_ARRAY, TEXTYPE_CUBE_ARRAY, TEXTYPE_1D_ARRAY, TEXTYPE_BUFFER, TEXTYPE_2D_MS };
static uint64_t bits(uint64_t w, int lo, int n) { return (w >> lo) & ((n == 64) ? ~0ull : ((1ull << n) - 1)); }
static const char *reg(Ctx *c, int r, char *buf) {
    if (r == RZ) return "0u";
    c->reg_used[r] = 1;
    sprintf(buf, "r%d", r);
    return buf;
}
#define R(r) reg(c, (r), alloca(16))

// sp(&c->body, fmt, ...) appends GLSL to the shader body; fail(c, fmt, ...) aborts the translation (call it, then return).
// c->glsl: true when emitting Vulkan GLSL (the only mode this card supports).
// c->reg_used[r] = 1 must be set for every register r the GLSL WRITES (R() already does it for the ones it names).

// Texture binding. index = bound cbuf offset (bits 36..48 of TEX-family instructions); type = TEXTYPE_*; the GLSL
// sampler for the returned slot s is named t<s> and is declared later with the slot's type (sampler2D, sampler2DArray,
// samplerCube, ...). Passing the same index with a different type/shadow than an earlier use fails the translation.
static int tex_slot(Ctx *c, uint32_t index, int type, bool shadow, bool array) {
    if (index >= 8192) return 0;
    if (c->tex_slot[index]) {
        int s = c->tex_slot[index] - 1;
        if (type >= 0 && c->tex_weak[s]) {
            ShaderTexture *t = &c->info->tex[s];
            t->type = (uint8_t)type;
            t->shadow = shadow;
            t->is_array = array;
            c->tex_weak[s] = false;
        } else if (c->glsl && type >= 0 && (c->info->tex[s].type != type || c->info->tex[s].shadow != shadow)) {
            fail(c, "texture %u used as two types", index);  // one GLSL sampler type per binding
        }
        return s;
    }
    /* ... allocates a new slot s ... */
}
// c->tex_slot[index] (0 = unused, else slot + 1) and c->info->tex[slot].shadow tell how an earlier instruction used it.

// The existing TXQ case, for the code style (one block per instruction inside the big if/else chain):
//     } else if (OPM(0xdf48000000000000ull, 0xfff8000000000000ull)) {  // TXQ
//         uint32_t index = (uint32_t)bits(w, 36, 13);
//         ...
//         int n = 0;
//         for (int i = 0; i < 4; i++)
//             if (mask & (1u << i)) { c->reg_used[d + n] = 1; sp(&c->body, "      r%d = q[%d];\n", d + n, i); n++; }
