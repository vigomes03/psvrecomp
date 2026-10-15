"""Experiment for 1.7: why do jump tables fall back to 'all labels' in the FINAL function partition?

Hypothesis: the fixpoint splits functions, so the address materialization (ADRP/ADD of the table base) lies before the
split piece's entry and isn't replayed. For each br that is unresolved with the final piece as window, retry with the
replay starting at the enclosing .eh_frame/symbol boundary (targets still required inside the final piece).
Usage: exp_jt.py <nso> <base>
"""
import bisect
import sys

import gen

nso, base = sys.argv[1], int(sys.argv[2], 0)
m = gen.Module('m', nso, base, 'c')
outer = sorted(set(m.boundaries()))

# final partition, as gen.main() computes it
start_set = set(outer)
for i, w in enumerate(m.words):
    if (w & 0xFC000000) == 0x94000000:
        t = m.lo + i * 4 + gen.sext26(w) * 4
        if m.in_text(t):
            start_set.add(t)
scanned = {}
while True:
    order = sorted(start_set)
    new = set()
    for i, a in enumerate(order):
        end = order[i + 1] if i + 1 < len(order) else m.hi
        if (a, end) not in scanned:
            scanned[(a, end)] = m.scan(a, end)
        new |= scanned[(a, end)][1] - start_set
    if not new:
        break
    start_set |= new
order = sorted(start_set)

unres = fixed = targets_outside = 0
for i, a in enumerate(order):
    end = order[i + 1] if i + 1 < len(order) else m.hi
    for br, tab in scanned[(a, end)][2].items():
        if tab != 'all':
            continue
        unres += 1
        o = outer[bisect.bisect_right(outer, br) - 1]
        oend_i = bisect.bisect_right(outer, br)
        oend = outer[oend_i] if oend_i < len(outer) else m.hi
        t = m.jump_table(br, o, oend)
        if t:
            if all(a <= x < end for x in t):
                fixed += 1
            else:
                targets_outside += 1
print(f'unresolved in final partition: {unres}')
print(f'  resolved replaying from the outer boundary, all targets in the piece: {fixed}')
print(f'  resolved but some targets fall in OTHER pieces: {targets_outside}')
print(f'  still unresolved: {unres - fixed - targets_outside}')
