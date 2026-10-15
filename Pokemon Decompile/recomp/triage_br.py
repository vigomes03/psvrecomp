"""Triage of unresolved computed `br` (jump tables gen.py can't resolve -> 'all labels' fallback).

Groups them by the mnemonic shape of the instructions before the br, with one example address per shape.
Usage: triage_br.py <nso> <base> [top]
"""
import bisect
import collections
import sys

import capstone
import gen

nso, base = sys.argv[1], int(sys.argv[2], 0)
top = int(sys.argv[3]) if len(sys.argv) > 3 else 15
m = gen.Module('m', nso, base, 'c')
cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
starts = sorted(set(m.boundaries()))
shapes, ex, n = collections.Counter(), {}, 0


def dis(a):
    d = list(cs.disasm(m.word(a).to_bytes(4, 'little'), a))
    return d[0] if d else None


for i, w in enumerate(m.words):
    if (w & 0xFFFFFC1F) != 0xD61F0000:  # br xN
        continue
    a = m.lo + i * 4
    j = bisect.bisect_right(starts, a) - 1
    entry = starts[j]
    end = starts[j + 1] if j + 1 < len(starts) else m.hi
    if not m.computed_target(a, entry) or m.jump_table(a, entry, end):
        continue
    n += 1
    win = [dis(b) for b in range(max(entry, a - 32), a + 4, 4)]
    key = ' '.join(d.mnemonic if d else '?' for d in win[-7:])
    shapes[key] += 1
    ex.setdefault(key, a)
print('unresolved computed br:', n)
for k, v in shapes.most_common(top):
    print(f'{v:5}  {k}   e.g. {ex[k]:#x}')
if len(sys.argv) > 4:
    a = int(sys.argv[4], 16)
    for b in range(a - 64, a + 8, 4):
        d = dis(b)
        print(f'  {b:#x}: {d.mnemonic} {d.op_str}' if d else f'  {b:#x}: ?')
