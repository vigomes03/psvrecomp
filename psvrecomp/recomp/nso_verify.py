"""Verify NSO segment SHA-256 hashes (header 0xA0..) against the decompressed segments: proves the extraction is intact."""
import hashlib
import struct
import sys

import lz4.block

if len(sys.argv) < 2:
    sys.exit('Usage: nso_verify.py <NSO> [NSO ...]')

failed = False
for p in sys.argv[1:]:
    d = open(p, 'rb').read()
    assert d[:4] == b'NSO0', p
    flags = struct.unpack_from('<I', d, 0xC)[0]
    res = []
    for i, (hoff, csz_off) in enumerate([(0x10, 0x60), (0x20, 0x64), (0x30, 0x68)]):
        foff, moff, size = struct.unpack_from('<III', d, hoff)
        csz = struct.unpack_from('<I', d, csz_off)[0]
        raw = d[foff:foff + csz]
        if (flags >> i) % 2:
            raw = lz4.block.decompress(raw, uncompressed_size=size)
        want = d[0xA0 + 0x20 * i: 0xC0 + 0x20 * i]
        res.append('ok' if hashlib.sha256(raw).digest() == want else 'BAD')
    print(p.replace('\\', '/').split('/')[-3:], 'flags', hex(flags), 'text/ro/data sha256:', res)
    failed |= 'BAD' in res

sys.exit(1 if failed else 0)
