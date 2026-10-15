"""Find the size real NVN gives each builder/state object: the SDK's own `nvn*SetDefaults` implementations zero the
object with a run of stores; report the highest byte offset stored (`str/stp ... [x0, #off]`) per function.

Usage: nvn_sizes.py <exefs_dir> [name filter]
"""
import re
import sys

from capstone import CS_ARCH_ARM64, CS_MODE_ARM, Cs

from layout import layout
from nso import Nso

exefs = sys.argv[1]
flt = sys.argv[2] if len(sys.argv) > 2 else 'SetDefaults'
base = {n: b for n, b, _, _ in layout(exefs)[0]}['sdk']
n = Nso(f'{exefs}/sdk')
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
for s in sorted(n.syms, key=lambda s: s[0]):
    name = s[0]
    if not (name.startswith('nvn') and flt in name and s[2] and (s[1] & 0xF) == 2):
        continue
    off = s[3]
    hi = 0
    regs = {'x0'}
    for i in md.disasm(bytes(n.image[off:off + 4 * 120]), base + off):
        if i.mnemonic in ('ret', 'b', 'br'):
            if i.mnemonic == 'b' and hi == 0:
                pass
            break
        m = re.match(r'mov (x\d+), x0$', f'{i.mnemonic} {i.op_str}')
        if m:
            regs.add(m.group(1))
        if i.mnemonic in ('str', 'stp', 'stur', 'strb', 'strh', 'stp', 'stnp') or i.mnemonic.startswith('st'):
            mm = re.search(r'\[(x\d+)(?:, #(-?0x[0-9a-f]+|-?\d+))?\]', i.op_str)
            if mm and mm.group(1) in regs:
                o = int(mm.group(2), 0) if mm.group(2) else 0
                width = 16 if i.mnemonic in ('stp', 'stnp') and i.op_str.startswith(('x', 'q')) else 8
                if i.op_str.startswith('q'):
                    width = 32 if i.mnemonic == 'stp' else 16
                if i.op_str.startswith('w'):
                    width = 8 if i.mnemonic == 'stp' else 4
                hi = max(hi, o + width)
    print(f'{name:55} highest store end {hi:#x}')
