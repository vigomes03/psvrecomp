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

// sp(&c->body, fmt, ...) appends one line of GLSL to the shader body; fail(c, fmt, ...) aborts the translation.

// Storage image for SUST / SURED: bound (handle at c[2][bound_offset * 4]) or bindless through a register that was
// loaded with MOV from the driver cbuf c[2] (what Pokémon's shaders do). Returns the image index i (GLSL `img<i>`).
// type: TEXTYPE_1D / 1D_ARRAY / 2D / 2D_ARRAY / 3D. NVN keeps image handles at c[2][0x120 + 8 * slot].
static int img_slot(Ctx *c, bool bound, uint32_t bound_offset, int handle_reg, int type) {
    uint32_t off;
    if (bound) {
        off = bound_offset * 4;
    } else {
        uint32_t t = handle_reg == RZ ? 0 : c->reg_cb[handle_reg];
        if (!(t & 0x80000000u) || ((t >> 16) & 0x1F) != 2) { fail(c, "bindless image handle not from c[2]"); return 0; }
        off = t & 0xFFFF;
    }
    if (type != TEXTYPE_1D && type != TEXTYPE_1D_ARRAY && type != TEXTYPE_2D && type != TEXTYPE_2D_ARRAY && type != TEXTYPE_3D) {
        fail(c, "image type %d", type);
        return 0;
    }
    for (int i = 0; i < c->info->nimg; i++)
        if (c->info->img[i].handle_offset == off) {
            if (c->info->img[i].type != type) fail(c, "image %#x used as two types", off);
            return i;
        }
    if (c->info->nimg >= 8) { fail(c, "too many images"); return 0; }
    ShaderTexture *t = &c->info->img[c->info->nimg];
    memset(t, 0, sizeof *t);
    t->handle_offset = off;
    t->type = (uint8_t)type;
    t->is_image = true;
    return c->info->nimg++;
}
