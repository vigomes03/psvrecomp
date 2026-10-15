"""Guest address -> nearest exported FUNC symbol (module:name+off), demangled with c++filt when available.

Usage: addr2sym.py <exefs_dir> <addr_hex> [...]      (bases from layout.py, so it matches the build of that dump)
"""
import bisect
import shutil
import subprocess
import sys

from layout import layout
from nso import Nso

exefs = sys.argv[1]
tab = []
for name, base, _, _ in layout(exefs)[0]:
    for s in Nso(f'{exefs}/{name}').exports():
        if (s[1] & 0xF) == 2:  # STT_FUNC
            tab.append((base + s[3], name, s[0]))
tab.sort()
keys = [t[0] for t in tab]
lines = []
for a in sys.argv[2:]:
    v = int(a, 16)
    k = bisect.bisect_right(keys, v) - 1
    lines.append(f'{v:x} {tab[k][1]}:{tab[k][2]}+{v - tab[k][0]:#x}' if k >= 0 else f'{v:x} ?')
out = '\n'.join(lines) + '\n'
cf = shutil.which('c++filt') or r'D:\msys64\ucrt64\bin\c++filt.exe'
try:
    out = subprocess.run([cf], input=out, capture_output=True, text=True).stdout
except OSError:
    pass
print(out, end='')
