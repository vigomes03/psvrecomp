// Excerpts of Pokemon Decompile/runtime/nvn/maxwell/translate.c
#define RZ 255
#define PT 7
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
static char *fmt_f(char *b, const char *e) { sprintf(b, "as_type<float>(%s)", e); return b; }

static const char *pred(Ctx *c, int p, bool neg, char *buf) {
    if (p == PT) return neg ? "false" : "true";
    c->pred_used[p] = 1;
    sprintf(buf, "%sp%d", neg ? "!" : "", p);
    return buf;
}
#define P(p, n) pred(c, (p), (n), alloca(16))
static void set_reg(Ctx *c, int r, const char *expr) {
    if (r == RZ) return;
    c->reg_used[r] = 1;
    sp(&c->body, "    r%d = %s;\n", r, expr);
}

static const char *fneg_abs(const char *e, bool neg, bool abs_, char *buf) {

// sp(&c->body, fmt, ...) appends a line of GLSL to the shader body.
// Existing ISETP handler (how predicates are written):
               OPM(0x3660000000000000ull, 0xfef0000000000000ull)) {  // ISETP
        char cmp[512];
        icmp_expr(cmp, (int)bits(w, 49, 3), R(a), B(false), bits(w, 48, 1));
        int p = (int)bits(w, 3, 3), q = (int)bits(w, 0, 3), bo = (int)bits(w, 45, 2);
        const char *pp = P((int)bits(w, 39, 3), bits(w, 42, 1));
        sp(&c->body, "    { bool cmp = %s; bool pp = %s;\n", cmp, pp);
        if (p != PT) { c->pred_used[p] = 1; sp(&c->body, "      p%d = cmp %s pp;\n", p, bool_op(bo)); }
        if (q != PT) { c->pred_used[q] = 1; sp(&c->body, "      p%d = !cmp %s pp;\n", q, bool_op(bo)); }
        sp(&c->body, "    }\n");
