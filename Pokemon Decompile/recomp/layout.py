"""Guest load layout of the Pokémon Violet v1.0.0 modules: the single source of truth for gen.py bases and the runtime loader.

Horizon's loader maps modules back to back in this order: rtld, main, subsdk*, sdk. We keep that order, start
at 0x7000000000 like LAS Recomp, and align each module to 2 MiB. The Zelda layout (sdk at +64 MiB) does NOT fit:
Pokémon's main is ~68 MiB.
Usage: python layout.py [exefs_dir]  -> prints the table (and checks the modules don't overlap)
"""
import os
import sys

from nso import Nso

GUEST_BASE = 0x7000000000
ALIGN = 0x200000
ORDER = ['main', 'subsdk0', 'sdk']  # rtld is replaced by host code (HLE), as in LAS Recomp


def layout(exefs):
    out, at = [], GUEST_BASE
    for name in ORDER:
        path = os.path.join(exefs, name)
        if not os.path.exists(path):
            continue
        n = Nso(path)
        out.append((name, at, n.size, n.build_id[:16]))
        at = (at + n.size + ALIGN - 1) & ~(ALIGN - 1)
    return out, at


if __name__ == '__main__':
    exefs = sys.argv[1] if len(sys.argv) > 1 else os.path.join('..', '..', 'dumps', 'base', 'exefs')
    mods, end = layout(exefs)
    for name, base, size, bid in mods:
        print(f'{name:8} base={base:#x} size={size:#x} ({size / 2**20:.1f} MiB) end={base + size:#x} build={bid}')
    print(f'modules end at {end:#x} ({(end - GUEST_BASE) / 2**20:.1f} MiB)')
