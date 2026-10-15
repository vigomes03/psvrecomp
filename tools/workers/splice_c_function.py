"""Splice top-level C function definitions from a worker's snippet into an existing source file.

Workers (qwen) produce only the functions a card asks for instead of re-emitting a 900-line file. For every
top-level definition in the snippet:
  - if the file has a definition with the same key, it is replaced in place (with its leading // comment block);
  - otherwise it is inserted right before the first REPLACED definition (so new helpers precede their users),
    or appended at the end when nothing was replaced.
Key = the name inside NVN(...)/SERVICE(..., fn)/HLE_FUNC, else the identifier before the first '('.
Exits 1 (file untouched) if the snippet has no definitions, a brace doesn't balance, or a key expected by --expect
is missing.

Usage: splice_c_function.py <target.c> <snippet.c> [--expect name1,name2] [--dry-run]
"""
import re
import sys

DEF_START = re.compile(r'^(?:NVN\((\w+)\)|SERVICE\("[^"]*",\s*(\w+)\)|(?:static\s+|inline\s+|extern\s+)*'
                       r'[A-Za-z_][\w\s\*]*?\b(\w+)\s*\([^;]*$)')


def strip_strings(line):
    return re.sub(r'"(\\.|[^"\\])*"|\'(\\.|[^\'\\])*\'', '""', line.split('//')[0])


def definitions(lines):
    """[(key, start, end)] of top-level function definitions; start includes the leading // comment block."""
    out, i, depth = [], 0, 0
    while i < len(lines):
        line = lines[i]
        m = DEF_START.match(line) if depth == 0 else None
        if m and not line.lstrip().startswith(('#', '//', 'typedef', 'struct', 'enum', 'return')):
            key = m.group(1) or m.group(2) or m.group(3)
            # find the opening brace (may be on a following line for multi-line signatures); bail on ';' first
            j, opened, d = i, False, 0
            while j < len(lines):
                s = strip_strings(lines[j])
                if not opened and ';' in s and '{' not in s:
                    break
                for ch in s:
                    if ch == '{':
                        d += 1
                        opened = True
                    elif ch == '}':
                        d -= 1
                if opened and d == 0:
                    break
                j += 1
            if opened and d == 0:
                start = i
                while start > 0 and lines[start - 1].lstrip().startswith('//'):
                    start -= 1
                out.append((key, start, j + 1))
                i = j + 1
                continue
            if opened:
                raise SystemExit(f'unbalanced braces in definition {key!r} starting at line {i + 1}')
        for ch in strip_strings(line):
            depth += ch == '{'
            depth -= ch == '}'
        i += 1
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    expect = []
    if '--expect' in sys.argv:
        expect = sys.argv[sys.argv.index('--expect') + 1].split(',')
        args = [a for a in args if a != sys.argv[sys.argv.index('--expect') + 1]]
    target, snippet = args[0], args[1]
    tl = open(target, encoding='utf-8').read().splitlines()
    sl = open(snippet, encoding='utf-8').read().splitlines()
    sdefs = definitions(sl)
    if not sdefs:
        raise SystemExit('snippet has no function definitions')
    keys = [k for k, _, _ in sdefs]
    missing = [e for e in expect if e not in keys]
    if missing:
        raise SystemExit(f'snippet lacks expected definitions: {missing} (has {keys})')
    tdefs = {k: (s, e) for k, s, e in definitions(tl)}
    replaced = [k for k in keys if k in tdefs]
    new = [k for k in keys if k not in tdefs]
    body = {k: sl[s:e] for k, s, e in sdefs}
    # top-level #defines outside any definition (e.g. a constant the new code uses) travel with the snippet:
    # they go right before the first spliced definition, unless the target already has the identical line
    covered = set()
    for _, s, e in sdefs:
        covered.update(range(s, e))
    existing = set(tl)
    defines = [l for i, l in enumerate(sl) if i not in covered and l.startswith('#define') and l not in existing]
    if defines:
        first = keys[0]
        body[first] = defines + [''] + body[first]
    # apply replacements bottom-up so earlier indices stay valid
    for k in sorted(replaced, key=lambda k: -tdefs[k][0]):
        s, e = tdefs[k]
        tl[s:e] = body[k]
    if new:
        block = []
        for k in new:
            block += body[k] + ['']
        if replaced:
            first = min(replaced, key=lambda k: tdefs[k][0])
            at = definitions(tl)
            at = next(s for k2, s, _ in at if k2 == first)
            tl[at:at] = block
        else:
            tl += [''] + block
    print(f'replaced: {replaced}\ninserted: {new}')
    if '--dry-run' not in sys.argv:
        open(target, 'w', encoding='utf-8', newline='\n').write('\n'.join(tl) + '\n')


if __name__ == '__main__':
    main()
