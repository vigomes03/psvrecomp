"""Maxwell opcode census of shaders translated by our recompiler (GLSL with `// pc X: <hex>` comments).

The opcode table is Eden's frontend/maxwell/maxwell.inc (reference only, read at run time; not copied).
usage: python maxwell_ops.py <file.glsl> [<file.glsl> ...]      -> opcode: count, first pc
       python maxwell_ops.py --hex 5c98078001ae0002              -> opcode of one instruction
"""
import re
import sys
from collections import Counter, defaultdict

INC = "D:/Dev/REA/ref/eden-master/eden/src/shader_recompiler/frontend/maxwell/maxwell.inc"


def load_table():
    pats = []
    for m in re.finditer(r'INST\((\w+),\s*"[^"]*",\s*"([01\- ]+)"\)', open(INC, encoding="utf-8").read()):
        bits = m.group(2).replace(" ", "")
        mask = val = 0
        for i, ch in enumerate(bits):
            b = 63 - i
            if ch != "-":
                mask |= 1 << b
                val |= (ch == "1") << b
        pats.append((m.group(1), mask, val, bin(mask).count("1")))
    pats.sort(key=lambda p: -p[3])  # most specific first (as Eden's decoder)
    return pats


def decode(pats, w):
    for name, mask, val, _ in pats:
        if w & mask == val:
            return name
    return "?"


def main():
    pats = load_table()
    if sys.argv[1] == "--hex":
        for h in sys.argv[2:]:
            print(h, decode(pats, int(h, 16)))
        return
    for path in sys.argv[1:]:
        cnt, first = Counter(), {}
        for m in re.finditer(r"// pc ([0-9a-f]+): ([0-9a-f]{16})", open(path, encoding="utf-8").read()):
            op = decode(pats, int(m.group(2), 16))
            cnt[op] += 1
            first.setdefault(op, m.group(1))
        print(f"== {path}: {sum(cnt.values())} instructions, {len(cnt)} opcodes")
        for op, n in sorted(cnt.items(), key=lambda kv: -kv[1]):
            print(f"  {op:16s} {n:5d}  first pc {first[op]}")


if __name__ == "__main__":
    main()
