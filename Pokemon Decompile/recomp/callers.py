"""Callers of a function (direct BL/B) in one module, plus a short disassembly window.

Usage: callers.py <module> <guest_addr_hex> [dis_from_hex dis_to_hex]
"""
import bisect
import struct
import sys

import capstone
from layout import layout
from nso import Nso

mod, target = sys.argv[1], int(sys.argv[2], 16)
base = {nm: b for nm, b, _, _ in layout('../../dumps/base/exefs')[0]}[mod]
n = Nso(f'../../dumps/base/exefs/{mod}')
names = {s[3]: s[0] for s in n.syms if s[2] and (s[1] & 0xF) == 2}
a = sorted(names)


def nm(o):
    i = bisect.bisect_right(a, o) - 1
    return f'{names[a[i]][:90]}+{o - a[i]:#x}' if i >= 0 else hex(o)


print('target:', nm(target - base))
t0, tl = n.text
W = struct.unpack_from(f'<{tl // 4}I', n.image, t0)
for k, w in enumerate(W):
    if (w & 0x7C000000) == 0x14000000:  # B / BL
        imm = w & 0x3FFFFFF
        if imm & 0x2000000:
            imm -= 0x4000000
        o = t0 + 4 * k
        if o + imm * 4 == target - base:
            print(f"  {'bl' if w >> 31 else 'b '} from {base + o:#x}  {nm(o)}")
if len(sys.argv) > 4:
    cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    lo, hi = int(sys.argv[3], 16) - base, int(sys.argv[4], 16) - base
    for x in cs.disasm(bytes(n.image[lo:hi]), base + lo):
        print(f'    {x.address:#x}: {x.mnemonic:7} {x.op_str}')
