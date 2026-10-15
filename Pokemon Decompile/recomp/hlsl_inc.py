"""Turn third_party/smaa/SMAA.hlsl into a C string literal include (same as LAS's Makefile rule for smaa_hlsl.inc).

Usage: hlsl_inc.py <SMAA.hlsl> <out.inc>
"""
import sys

src, out = sys.argv[1], sys.argv[2]
data = open(src, 'rb').read().replace(b'\r', b'')
text = ''.join(chr(b) if b < 0x80 else '?' for b in data)
lines = text.split('\n')
if lines and lines[-1] == '':
    lines.pop()
with open(out, 'w', encoding='ascii', newline='\n') as f:
    for line in lines:
        f.write('"' + line.replace('\\', '\\\\').replace('"', '\\"') + '\\n"\n')
print(f'{out}: {len(lines)} lines')
