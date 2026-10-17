"""Symbolize a pvhost crash backtrace: pvgame.dll+OFF -> f_<guest addr>+delta (from the lld map of run_boot.sh).

Usage: symbolize.py <pvgame.map> <boot.log>
"""
import bisect
import re
import sys

syms = []
for line in open(sys.argv[1], encoding='utf-8', errors='replace'):
    m = re.match(r'\s*([0-9a-f]{8,16})\s+[0-9a-f]+\s+[0-9]+\s+(f_[0-9a-f]+)\s*$', line)  # RVA size align symbol
    if m:
        syms.append((int(m.group(1), 16), m.group(2)))
syms.sort()
addrs = [a for a, _ in syms]
IMAGE_BASE = 0  # map addresses are RVAs
for line in open(sys.argv[2], encoding='utf-8', errors='replace'):
    m = re.search(r'pvgame\.dll\+([0-9a-f]+)', line)
    if m:
        va = IMAGE_BASE + int(m.group(1), 16)
        i = bisect.bisect_right(addrs, va) - 1
        line = line.rstrip() + (f'   {syms[i][1]}+{va - addrs[i]:#x}' if i >= 0 else '') + '\n'
    sys.stdout.write(line)
