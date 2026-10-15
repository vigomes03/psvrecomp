// Excerpts of Pokemon Decompile/runtime/nvn/maxwell/translate.c (registers are GLSL uint r0..r254)
#define RZ 255
#define LMEM_WORDS 256  // local memory per invocation (1 KB)
#define PT 7
    int ipa_mode;  // interpolation mode of the IPA being translated (-1 for plain loads)
    // GLSL (fields kept last: the MSL path's layout, including its out-of-range reg_used writes, is unchanged)
    bool glsl;               // emit Vulkan GLSL: dialect-specific constructs here, the rest via glsl_rewrite()
    bool uses_gmem_store;    // STG present: the gmem buffer is not readonly
    uint32_t cbuf_need[18];  // highest constant vec4 index + 1 per cbuf (array size of the GLSL block)

static uint64_t bits(uint64_t w, int lo, int n) { return (w >> lo) & ((n == 64) ? ~0ull : ((1ull << n) - 1)); }
static int64_t sbits(uint64_t w, int lo, int n) {
    int64_t v = (int64_t)bits(w, lo, n);
    return (v & (1ll << (n - 1))) ? v - (1ll << n) : v;
}

// ------------------------------------------------------------------ operands
static const char *reg(Ctx *c, int r, char *buf) {
    if (r == RZ) return "0u";
    c->reg_used[r] = 1;
    sprintf(buf, "r%d", r);
    return buf;
}

#define R(r) reg(c, (r), alloca(16))

// maxwell_gmem_base / maxwell_gmem_size: globals (uint64_t) = guest address range of the gmem buffer.
// GLSL buffer declared elsewhere: layout(std430) buffer GMem { uint w[]; } gmem_;
// Existing LDG/STG handler inside emit_insn (a = bits 8..15, d = bits 0..7 already decoded there):
    } else if (OPM(0xeed0000000000000ull, 0xfff8000000000000ull) || OPM(0xeed8000000000000ull, 0xfff8000000000000ull)) {  // LDG / STG
        bool store = bits(w, 51, 1);
        bool wide = bits(w, 45, 1);
        int size = (int)bits(w, 48, 3);
        int64_t off = sbits(w, 20, 24);
        c->info->uses_gmem = true;
        char addr[256];
        if (a == RZ) sprintf(addr, "ulong(%lld)", (long long)off);
        else if (wide) sprintf(addr, "((ulong(%s) << 32 | ulong(%s)) + ulong(%lld))", R(a + 1), R(a), (long long)off);
        else sprintf(addr, "(ulong(%s) + ulong(%lld))", R(a), (long long)off);
        sp(&c->body, "    { ulong ga = %s - 0x%llxul; bool ok = ga < 0x%llxul;\n", addr,
           (unsigned long long)maxwell_gmem_base, (unsigned long long)maxwell_gmem_size);
        static const char *const ld_small[] = {"uint(gmem[ga])", "uint(int(char(gmem[ga])))",
                                               "uint(*(device ushort *)(gmem + ga))", "uint(int(*(device short *)(gmem + ga)))"};
        int nw = size == 5 ? 2 : size >= 6 ? 4 : 1;
        if (c->glsl) {  // gmem_.w[]: 32-bit words; sub-word accesses within the containing word
            ...
            } else {
                c->uses_gmem_store = true;
                    for (int k = 0; k < nw; k++)
                        sp(&c->body, "      if (ok) gmem_.w[uint(ga >> 2) + %du] = %s;\n", k, R(d == RZ ? RZ : d + k));
        }
        sp(&c->body, "    }\n");
