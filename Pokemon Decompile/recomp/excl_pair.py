"""LDXP/LDAXP/STXP/STLXP (64-bit exclusive pairs) -> C. Worker W02 (qwen3-coder-64k, 2 tries), reviewed by Claude."""
from lifter import Insn, Unsupported, bits, X, XS, set_reg

def lift_excl_pair(w, pc):
    sz = bits(w, 30, 1)
    if sz != 1:
        raise Unsupported('excl pair 32')
    
    L = bits(w, 22, 1)
    o2 = bits(w, 23, 1)
    if o2 != 0:
        raise Unsupported('cas pair')
        
    o1 = bits(w, 21, 1)
    if o1 != 1:
        raise Unsupported('excl pair')
    
    rs = bits(w, 16, 5)
    o0 = bits(w, 15, 1)
    rt2 = bits(w, 10, 5)
    rn = bits(w, 5, 5)
    rt = bits(w, 0, 5)
    
    if L == 1:  # load
        acquire = o0 == 1
        if acquire:
            return Insn('op', '{ uint64_t lo, hi; ldaxp64(c, %s, &lo, &hi); %s %s }' % 
                       (XS(rn), set_reg(1, rt, 'lo'), set_reg(1, rt2, 'hi')))
        else:
            return Insn('op', '{ uint64_t lo, hi; ldxp64(c, %s, &lo, &hi); %s %s }' % 
                       (XS(rn), set_reg(1, rt, 'lo'), set_reg(1, rt2, 'hi')))
    else:  # store
        release = o0 == 1
        if release:
            return Insn('op', '{ uint32_t st = stlxp64(c, %s, %s, %s); %s }' % 
                       (XS(rn), X(rt), X(rt2), set_reg(0, rs, 'st')))
        else:
            return Insn('op', '{ uint32_t st = stxp64(c, %s, %s, %s); %s }' % 
                       (XS(rn), X(rt), X(rt2), set_reg(0, rs, 'st')))
