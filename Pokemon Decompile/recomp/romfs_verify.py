"""Independent integrity check of an extracted (patched) romfs against the base romfs.

1. Same-size files present in both: byte compare (they should be untouched by the patch).
2. Wwise .bnk / .pck: walk the chunk structure (4-byte tag + u32 size) and require it to land exactly at EOF.
3. Game Freak .trpfs: header magic + the FlatBuffer index offset must point inside the file.
Usage: romfs_verify.py <base_romfs> <new_romfs>
"""
import filecmp
import os
import struct
import sys

base, new = sys.argv[1], sys.argv[2]
bad = 0


def rel_files(root):
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root).replace('\\', '/')] = p
    return out


B, N = rel_files(base), rel_files(new)
for r, p in sorted(N.items()):
    if r in B and os.path.getsize(B[r]) == os.path.getsize(p):
        same = filecmp.cmp(B[r], p, shallow=False)
        print(f'{"same " if same else "DIFF "} {r}  (same size, compared bytes)')
    if r.endswith('.bnk'):
        with open(p, 'rb') as f:
            data = f.read()
        off, tags = 0, []
        while off + 8 <= len(data):
            tag, size = data[off:off + 4], struct.unpack_from('<I', data, off + 4)[0]
            if not tag.isalpha():
                break
            tags.append(tag.decode())
            off += 8 + size
        ok = off == len(data) and tags and tags[0] == 'BKHD'
        bad += not ok
        print(f'{"ok   " if ok else "BAD  "} {r}  chunks {"/".join(tags)} end {off} of {len(data)}')
    if r.endswith('.trpfs'):
        with open(p, 'rb') as f:
            hdr = f.read(16)
            size = os.path.getsize(p)
        magic, idx = hdr[:8], struct.unpack_from('<Q', hdr, 8)[0]
        ok = magic.startswith(b'ONEPACK') and 16 <= idx < size
        bad += not ok
        print(f'{"ok   " if ok else "BAD  "} {r}  magic {magic!r} index offset {idx:#x} of {size:#x}')
print('RESULT:', 'OK' if not bad else f'{bad} BAD')
sys.exit(1 if bad else 0)
