"""Find instructions by encoding mask across the modules and name their enclosing symbol (when there is one).

Usage: find_insn.py <mask_hex> <value_hex> [modules...]   e.g. msr tpidr_el0, xN:  find_insn.py FFFFFFE0 D51BD040
"""
import bisect
import struct
import sys

from nso import Nso
from layout import layout

mask, val = int(sys.argv[1], 16), int(sys.argv[2], 16)
mods = sys.argv[3:] or ['main', 'subsdk0', 'sdk']
bases = {name: base for name, base, _, _ in layout('../../dumps/base/exefs')[0]}
for mod in mods:
    n = Nso(f'../../dumps/base/exefs/{mod}')
    names = {s[3]: s[0] for s in n.syms if s[2] and (s[1] & 0xF) == 2}
    a = sorted(names)
    t0, tl = n.text
    words = struct.unpack_from(f'<{tl // 4}I', n.image, t0)
    for k, w in enumerate(words):
        if (w & mask) == val:
            off = t0 + 4 * k
            i = bisect.bisect_right(a, off) - 1
            sym = f'{names[a[i]][:90]}+{off - a[i]:#x}' if i >= 0 else '?'
            print(f'{mod:8} {bases[mod] + off:#x}  {sym}')
