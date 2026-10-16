"""Name a GLSL override by content hash: python glsl_hash.py <saved glsl> -> prints s<fnv1a64>_<suffix>.glsl.
The translator hashes the in-memory source (LF); build/glsl files are written in text mode (CRLF on Windows)."""
import sys, os
def fnv(b):
    h = 0xcbf29ce484222325
    for x in b: h = ((h ^ x) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h
p = sys.argv[1]
src = open(p, 'rb').read().replace(b'\r\n', b'\n')
suffix = os.path.basename(p).rsplit('_', 1)[1]
print('s%016x_%s' % (fnv(src), suffix))
