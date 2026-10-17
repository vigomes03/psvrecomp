"""Name the target of a PLT stub (adrp x16 / ldr x17,[x16,#off] / add / br x17) via the module's JMPREL relocations.

Usage: plt_name.py <exefs_dir> <module> <guest_addr_hex> [more addrs...]   (bases from layout.py)
"""
import struct
import sys

from layout import layout
from nso import Nso

exefs, mod = sys.argv[1], sys.argv[2]
base = {n: b for n, b, _, _ in layout(exefs)[0]}[mod]
n = Nso(f'{exefs}/{mod}')
img = n.image
by_got = {}
for r in n.relocs:  # (offset, type, sym index, addend)
    off, typ, si = r[0], r[1], r[2]
    if typ in (1026, 1025) and si:  # R_AARCH64_JUMP_SLOT / GLOB_DAT
        by_got[off] = n.syms[si][0]


def u32(o):
    return struct.unpack_from('<I', img, o)[0]


for a in sys.argv[3:]:
    pc = int(a, 16) - base
    w0, w1 = u32(pc), u32(pc + 4)
    if (w0 & 0x9F00001F) != 0x90000010:
        print(a, 'not a PLT stub (no adrp x16)')
        continue
    page = ((pc >> 12) << 12) + ((((w0 >> 5) & 0x7FFFF) << 2 | (w0 >> 29) & 3) << 12)
    got = page + ((w1 >> 10) & 0xFFF) * 8
    print(a, f'GOT {base + got:#x}', by_got.get(got, '?'))
