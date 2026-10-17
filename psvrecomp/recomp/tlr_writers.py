"""Find `mrs xA, tpidrro_el0` followed (within 8 insns) by a store to [xA, #off] — who writes a TLR field.

Usage: tlr_writers.py <module> <off_hex>
"""
import bisect
import struct
import sys

import capstone
from layout import layout
from nso import Nso

mod, off = sys.argv[1], int(sys.argv[2], 16)
base = {nm: b for nm, b, _, _ in layout('../../dumps/base/exefs')[0]}[mod]
n = Nso(f'../../dumps/base/exefs/{mod}')
names = {s[3]: s[0] for s in n.syms if s[2] and (s[1] & 0xF) == 2}
a = sorted(names)
cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
t0, tl = n.text
W = struct.unpack_from(f'<{tl // 4}I', n.image, t0)
for k, w in enumerate(W):
    if (w & 0xFFFFFFE0) != 0xD53BD060:  # mrs xN, tpidrro_el0
        continue
    o = t0 + 4 * k
    win = list(cs.disasm(bytes(n.image[o:o + 36]), base + o))
    reg = win[0].op_str.split(',')[0]
    for x in win[1:]:
        if x.mnemonic.startswith('st') and f'[{reg}, #{off:#x}]' in x.op_str:
            i = bisect.bisect_right(a, o) - 1
            print(f'{base + o:#x} {names[a[i]][:90]}+{o - a[i]:#x}: {x.mnemonic} {x.op_str}')
