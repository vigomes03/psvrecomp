"""Backward def chain (slice) of a register in a GLSL shader produced by our Maxwell translator (card W20).

usage: python glsl_slice.py <file> --pc <hex> --reg rN [--depth D]
Prints one JSON object per definition: reg, pc, line (1-based), pred, stmt, uses, depth. Control flow is ignored
(text order); a predicated definition keeps the walk going, an unpredicated one stops it; no definition -> pc null.
(Written by Claude after two rejected qwen attempts: lab/arquivo/w20/.)
"""
import argparse
import json
import re
import sys

PC_RE = re.compile(r'^\s*//\s*pc\s+([0-9a-fA-F]+):')
IF_RE = re.compile(r'^\s*if\s*\((!?p\d+)\)\s*\{\s*$')
ASSIGN_RE = re.compile(r'^\s*(r\d+)\s*=(?!=)\s*(.*);\s*$')
BLOCK_RE = re.compile(r'^\s*\{\s*(?:u?vec4\s+t|uint\s+lv|uvec4\s+t)\s*=')
REG_RE = re.compile(r'\br(\d+)\b')


def regs(text):
    return sorted({'r' + n for n in REG_RE.findall(text)}, key=lambda r: int(r[1:]))


def parse(lines):
    """-> list of defs in text order: dict(reg, pc, line, pred, stmt, uses); and the line of each pc comment."""
    defs, pc_line = [], {}
    pc = None
    pred = None          # predicate of the open `if (pK) {` block
    block_uses = None    # registers of the open texture block's first line
    started = False
    for i, ln in enumerate(lines):
        if not started:
            started = bool(re.match(r'^\s*switch\s*\(', ln))
            continue
        m = PC_RE.match(ln)
        if m:
            pc = m.group(1).lower()
            pc_line.setdefault(pc, i)
            pred = None
            block_uses = None
            continue
        m = IF_RE.match(ln)
        if m:
            pred = m.group(1)
            continue
        if BLOCK_RE.match(ln):
            block_uses = regs(ln.split('=', 1)[1])
            continue
        if ln.strip() == '}':
            if block_uses is not None:
                block_uses = None
            else:
                pred = None
            continue
        m = ASSIGN_RE.match(ln)
        if m and pc is not None:
            uses = block_uses if block_uses is not None else regs(m.group(2))
            defs.append(dict(reg=m.group(1), pc=pc, line=i + 1, pred=pred, stmt=ln.strip(), uses=uses))
    return defs, pc_line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--pc', required=True)
    ap.add_argument('--reg', required=True)
    ap.add_argument('--depth', type=int, default=8)
    a = ap.parse_args()
    lines = open(a.file, encoding='utf-8', errors='replace').read().split('\n')
    defs, pc_line = parse(lines)
    pc = a.pc.lower().removeprefix('0x')
    if pc not in pc_line:
        print('pc %s not found' % pc, file=sys.stderr)
        return 2
    # defs[:end] = the target instruction's own definitions and everything before it
    end = 0
    while end < len(defs) and (defs[end]['line'] - 1 < pc_line[pc] or defs[end]['pc'] == pc):
        end += 1
    seen = set()

    def walk(reg, end, depth):
        for k in range(end - 1, -1, -1):
            d = defs[k]
            if d['reg'] != reg:
                continue
            key = (reg, d['pc'])
            if key not in seen:
                seen.add(key)
                print(json.dumps(dict(d, depth=depth)))
                if depth < a.depth:
                    for u in d['uses']:
                        walk(u, k, depth + 1)
            if d['pred'] is None:
                return
        if (reg, None) not in seen:
            seen.add((reg, None))
            print(json.dumps(dict(reg=reg, pc=None, line=None, pred=None, stmt=None, uses=[], depth=depth)))

    walk(a.reg, end, 0)
    return 0


if __name__ == '__main__':
    sys.exit(main())
