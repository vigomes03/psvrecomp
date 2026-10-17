"""Per-instruction replacements applied by gen.py (guest address -> function(gen, addr) returning C code).

Pokémon Violet: empty until we have a reason to patch. Rule inherited from LAS Recomp: every patch function
checks the ORIGINAL instruction word at its address and fails loudly if it differs (wrong build / wrong address),
e.g.:

    def _example(gen, a):
        w = struct.unpack_from('<I', gen.nso.image, a - gen.base)[0]
        assert w == 0xbd457369, hex(w)  # ldr s9, [x27, #0x570]
        return '/* replacement C */'

Patches are tied to one build id (docs/roadmap/achados-fase-0.md).
"""
import struct  # noqa: F401 (used by patch functions)

PATCHES = {}
