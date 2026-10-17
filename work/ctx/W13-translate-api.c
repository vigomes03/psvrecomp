// Excerpts of psvrecomp/runtime/nvn/maxwell/translate.c (the file the snippet is spliced into)

#define RZ 255
static uint64_t bits(uint64_t w, int lo, int n) { return (w >> lo) & ((n == 64) ? ~0ull : ((1ull << n) - 1)); }
static int64_t sbits(uint64_t w, int lo, int n) {
    int64_t v = (int64_t)bits(w, lo, n);
    return (v & (1ll << (n - 1))) ? v - (1ll << n) : v;
}

static void fail(Ctx *c, const char *fmt, ...) {
static const char *reg(Ctx *c, int r, char *buf) {
    if (r == RZ) return "0u";
    c->reg_used[r] = 1;
    sprintf(buf, "r%d", r);
    return buf;
}

#define R(r) reg(c, (r), alloca(16))
#define F(expr) fmt_f(alloca(512), (expr))

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
    bool weak = type < 0;
    if (weak) type = TEXTYPE_2D;
    int s = c->info->ntex++;
    if (s >= 31) { fail(c, "too many textures"); return 0; }
    c->tex_slot[index] = s + 1;
    c->tex_weak[s] = weak;
    ShaderTexture *t = &c->info->tex[s];
    t->handle_offset = index * 4;
    t->type = (uint8_t)type;
    t->shadow = shadow;
    t->is_array = array;
    return s;
}

// Write texture results: component mask selects which of r,g,b,a go to consecutive registers.
static void write_tex_result(Ctx *c, int slot, const char *call, uint32_t mask, int d0, int d1, bool texs, bool f16) {
    sp(&c->body, "    { float4 t = %s;\n", call);
    (void)slot;
    if (f16) {
        // TEXS/TLDS .F16: components (in mask order) packed as half pairs into d0 (lo, hi) and d1 (lo, hi)
        int comps[4], n = 0;
        for (int comp = 0; comp < 4; comp++) if (mask & (1u << comp)) comps[n++] = comp;
        char v[4][16];
        for (int i = 0; i < 4; i++) { if (i < n) sprintf(v[i], "t[%d]", comps[i]); else strcpy(v[i], "0.0f"); }
        const char *pk = c->glsl ? "      r%d = packHalf2x16(vec2(%s, %s));\n" : "      r%d = as_type<uint>(half2(half(%s), half(%s)));\n";
        if (d0 != RZ) { c->reg_used[d0] = 1; sp(&c->body, pk, d0, v[0], v[1]); }
        if (d1 != RZ) { c->reg_used[d1] = 1; sp(&c->body, pk, d1, v[2], v[3]); }
        sp(&c->body, "    }\n");
        return;
    }
    int regs[4], n = 0;
    if (texs) {
        // TEXS: up to two components in d0/d0+1, two more in d1/d1+1
        int out[4] = {d0, d0 == RZ ? RZ : d0 + 1, d1, d1 == RZ ? RZ : d1 + 1};
        for (int i = 0; i < 4; i++) regs[i] = out[i];
    } else {
        for (int i = 0; i < 4; i++) regs[i] = d0 == RZ ? RZ : d0 + i;
    }
    for (int comp = 0; comp < 4; comp++) {
        if (!(mask & (1u << comp))) continue;
        int r = regs[n++];
        if (r != RZ) { c->reg_used[r] = 1; sp(&c->body, "      r%d = as_type<uint>(t[%d]);\n", r, comp); }
    }
    sp(&c->body, "    }\n");
}

// GLSL texture lookup on slot `slot` (its type is final here: a conflicting use fails in tex_slot).
// co: coordinate expressions (1 for 1D, 2 for 2D, 3 for 3D / cube), layer: uint expression or NULL, dref: depth
// reference or NULL, lod_kind 0 implicit / 1 level / 2 bias (lod), off: ivec2 texel offset or NULL.
// GLSL offsets must be constants, so register offsets move the coordinates by offset / size of the level
// (level 0 for implicit-LOD lookups). Non-fragment stages have no implicit LOD: level 0 (+ bias).
static void glsl_sample(Ctx *c, char *out, int slot, const char *const *co, const char *layer, const char *dref,
                        int lod_kind, const char *lod, const char *off) {
    if (c->fail) { strcpy(out, "vec4(0.0f)"); return; }  // e.g. a type conflict: tex[slot] is not this lookup's type
    const ShaderTexture *t = &c->info->tex[slot];
    int type = t->type;
    bool cube = type == TEXTYPE_CUBE || type == TEXTYPE_CUBE_ARRAY;
    int n = (type == TEXTYPE_1D || type == TEXTYPE_1D_ARRAY) ? 1 : (type == TEXTYPE_2D || type == TEXTYPE_2D_ARRAY) ? 2 : 3;
    if (c->stage != STAGE_FRAGMENT && lod_kind != 1) {
        if (lod_kind == 0) lod = "0.0f";
        lod_kind = 1;
    }
    if (t->shadow && type == TEXTYPE_3D) { fail(c, "3d shadow texture"); strcpy(out, "vec4(0.0f)"); return; }
    if (layer && type != TEXTYPE_1D_ARRAY && type != TEXTYPE_2D_ARRAY && type != TEXTYPE_CUBE_ARRAY) {
        fail(c, "array lookup on a 3d texture");  // TEX .3D with the array bit
        strcpy(out, "vec4(0.0f)");
        return;
    }
    char L[600], xs[1600], P[2000];
    if (lod_kind == 1) snprintf(L, sizeof L, "int(%s)", lod); else strcpy(L, "0");
    if (n == 1) {
        if (off) snprintf(xs, sizeof xs, "(%s + float((%s).x) / float(tsize%d(%s).x))", co[0], off, slot, L);
        else snprintf(xs, sizeof xs, "%s", co[0]);
    } else if (n == 2) {
        if (off) snprintf(xs, sizeof xs, "(vec2(%s, %s) + vec2(%s) / vec2(tsize%d(%s).xy))", co[0], co[1], off, slot, L);
        else snprintf(xs, sizeof xs, "vec2(%s, %s)", co[0], co[1]);
    } else {
        if (off && !cube) snprintf(xs, sizeof xs, "vec3(vec2(%s, %s) + vec2(%s) / vec2(tsize%d(%s).xy), %s)", co[0], co[1], off, slot, L, co[2]);
        else snprintf(xs, sizeof xs, "vec3(%s, %s, %s)", co[0], co[1], co[2]);  // cube lookups take no offset
    }
    const char *extra = NULL;  // separate compare argument (cube array shadow)
    if (!t->shadow) {
        if (layer) snprintf(P, sizeof P, "vec%d(%s, float(%s))", n + 1, xs, layer);
        else snprintf(P, sizeof P, "%s", xs);
    } else if (type == TEXTYPE_CUBE_ARRAY) {
        snprintf(P, sizeof P, "vec4(%s, float(%s))", xs, layer ? layer : "0u");
        extra = dref;
    } else if (type == TEXTYPE_1D) {
        snprintf(P, sizeof P, "vec3(%s, 0.0f, %s)", xs, dref);
    } else if (layer) {
        snprintf(P, sizeof P, "vec%d(%s, float(%s), %s)", n + 2, xs, layer, dref);
    } else {
        snprintf(P, sizeof P, "vec%d(%s, %s)", n + 1, xs, dref);
    }
    char e[2000], ex[300] = "";
    if (extra) snprintf(ex, sizeof ex, ", %s", extra);
    if (lod_kind == 0) snprintf(e, sizeof e, "texture(t%d, %s%s)", slot, P, ex);
    else if (lod_kind == 1) snprintf(e, sizeof e, "textureLod(t%d, %s%s, %s)", slot, P, ex, lod);
    else snprintf(e, sizeof e, "texture(t%d, %s%s, %s)", slot, P, ex, lod);
    if (t->shadow) sprintf(out, "vec4(%s)", e);
    else strcpy(out, e);
}

// TEXS / TLDS in GLSL (same slot allocation order and result layout as the MSL switch in emit_texs)
static bool glsl_texs(Ctx *c, uint64_t w, bool fetch, int *slot_out, char *call, const char *A, const char *A1,
                      const char *Bv, const char *B1) {
    uint32_t index = (uint32_t)bits(w, 36, 13);
    int info = (int)bits(w, 53, 4);
    int slot;
    const char *co[3];
    char fa[64], fa1[64], fb[64], fb1[64];
    sprintf(fa, "as_type<float>(%s)", A); sprintf(fa1, "as_type<float>(%s)", A1);
    sprintf(fb, "as_type<float>(%s)", Bv); sprintf(fb1, "as_type<float>(%s)", B1);
    if (!fetch) {
        switch (info) {
        case 0: slot = tex_slot(c, index, TEXTYPE_1D, false, false); co[0] = fa;
            glsl_sample(c, call, slot, co, NULL, NULL, 0, NULL, NULL); break;
        case 1: slot = tex_slot(c, index, TEXTYPE_2D, false, false); co[0] = fa; co[1] = fb;
            glsl_sample(c, call, slot, co, NULL, NULL, 0, NULL, NULL); break;
        case 2: slot = tex_slot(c, index, TEXTYPE_2D, false, false); co[0] = fa; co[1] = fb;
    ... (rest of glsl_texs)

static void emit_texs(Ctx *c, uint64_t w, bool fetch) {
    int d0 = (int)bits(w, 0, 8), d1 = (int)bits(w, 28, 8), a = (int)bits(w, 8, 8), b = (int)bits(w, 20, 8);
    uint32_t index = (uint32_t)bits(w, 36, 13);
    int info = (int)bits(w, 53, 4);
    int msel = (int)bits(w, 50, 3);
    uint32_t mask;
    if (d1 == RZ) {
        static const uint32_t m2[] = {1, 2, 4, 8, 3, 9, 10, 12};
        mask = m2[msel];
    } else {
        static const uint32_t m4[] = {7, 11, 13, 14, 15, 15, 15, 15};
        mask = m4[msel];
    }
    char ra[16], ra1[16], rb[16], rb1[16];
    const char *A = reg(c, a, ra), *A1 = reg(c, a == RZ ? RZ : a + 1, ra1), *Bv = reg(c, b, rb),
               *B1 = reg(c, b == RZ ? RZ : b + 1, rb1);
    char call[1024];
    int slot;
    if (c->glsl) {
        char gcall[4096];
        if (!glsl_texs(c, w, fetch, &slot, gcall, A, A1, Bv, B1)) return;
        write_tex_result(c, slot, gcall, mask, d0, d1, true, !bits(w, 59, 1));
        return;
    }
    ... (MSL branch omitted: this card is GLSL only)
