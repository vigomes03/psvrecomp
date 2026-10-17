"""Disassemble guest code of one module (bases from layout.py for that dump).

Usage: disas.py <exefs_dir> <module> <addr_hex> [count=40] [--before N]   (--before: start N instructions earlier)
"""
import sys

from capstone import CS_ARCH_ARM64, CS_MODE_ARM, Cs

from layout import layout
from nso import Nso

args = [a for a in sys.argv[1:] if not a.startswith('--')]
before = int(sys.argv[sys.argv.index('--before') + 1]) if '--before' in sys.argv else 0
if before:
    args = [a for a in args if a != str(before)]
exefs, mod, addr = args[0], args[1], int(args[2], 16)
count = int(args[3]) if len(args) > 3 else 40
base = {n: b for n, b, _, _ in layout(exefs)[0]}[mod]
img = Nso(f'{exefs}/{mod}').image
start = addr - 4 * before
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
for i in md.disasm(bytes(img[start - base:start - base + 4 * (count + before)]), start):
    print(f'{"=>" if i.address == addr else "  "} {i.address:x}: {i.mnemonic} {i.op_str}')
