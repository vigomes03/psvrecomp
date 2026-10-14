"""Acceptance test for W01/W02 (LDXP/LDAXP/STXP/STLXP, 64-bit pairs).

1. Codegen: lift_excl_pair() output == the card's table (whitespace-insensitive).
2. Semantics vs Unicorn: for random registers/memory, run the 2-instruction sequence
   `ld(a)xp xA, xB, [xN]` ; `st(l)xp wS, xC, xD, [xN]` in Unicorn and in the lifted C (compiled with clang),
   then compare X registers and the 16 bytes of memory. Plus: a store without a prior load must fail (status 1, no write).
Usage: test_excl_pair.py [cases]   (clang on PATH)
"""
import os, random, re, struct, subprocess, sys
import unicorn as uc
from unicorn import arm64_const as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'recomp'))
from excl_pair import lift_excl_pair  # noqa: E402
from lifter import Unsupported  # noqa: E402

TABLE = {
    0xc87f2401: '{ uint64_t lo, hi; ldxp64(c, c->x[0], &lo, &hi); c->x[1] = (uint64_t)(lo); c->x[9] = (uint64_t)(hi); }',
    0xc87fa7e1: '{ uint64_t lo, hi; ldaxp64(c, c->sp, &lo, &hi); c->x[1] = (uint64_t)(lo); c->x[9] = (uint64_t)(hi); }',
    0xc8222401: '{ uint32_t st = stxp64(c, c->x[0], c->x[1], c->x[9]); c->x[2] = (uint32_t)(st); }',
    0xc822ffe1: '{ uint32_t st = stlxp64(c, c->sp, c->x[1], 0ull); c->x[2] = (uint32_t)(st); }',
}
norm = lambda s: re.sub(r'\s+', '', s)
fails = 0
for w, want in TABLE.items():
    ins = lift_excl_pair(w, 0)
    got = ins.code
    if ins.kind != 'op' or norm(got) != norm(want):  # gen.py only emits kind 'op'
        got = f'[kind={ins.kind}] ' + got
        fails += 1
        print(f'CODEGEN {w:#x}\n  got  {got}\n  want {want}')
try:
    lift_excl_pair(0x887f2401, 0)
    fails += 1
    print('CODEGEN 0x887f2401: expected Unsupported')
except Unsupported:
    pass
print(f'codegen: {5 - fails}/5 ok')

MEM = 0x10000


def enc_ld(acq, rt, rt2, rn):
    return 0xc87f0000 | acq << 15 | rt2 << 10 | rn << 5 | rt


def enc_st(rel, rs, rt, rt2, rn):
    return 0xc8200000 | rs << 16 | rel << 15 | rt2 << 10 | rn << 5 | rt


def unicorn_run(words, regs, mem16):
    mu = uc.Uc(uc.UC_ARCH_ARM64, uc.UC_MODE_ARM)
    mu.mem_map(0, 0x1000)
    mu.mem_map(MEM, 0x1000)
    mu.mem_write(0, b''.join(struct.pack('<I', w) for w in words))
    mu.mem_write(MEM, mem16)
    for i in range(31):
        mu.reg_write(A.UC_ARM64_REG_X0 + i if i < 29 else (A.UC_ARM64_REG_X29 if i == 29 else A.UC_ARM64_REG_X30), regs[i])
    mu.emu_start(0, 4 * len(words))
    out = [mu.reg_read(A.UC_ARM64_REG_X0 + i if i < 29 else (A.UC_ARM64_REG_X29 if i == 29 else A.UC_ARM64_REG_X30))
           for i in range(31)]
    return out, bytes(mu.mem_read(MEM, 16))


def main():
    global fails
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    r = random.Random(1)
    cases = []
    for k in range(n):
        regs = [r.getrandbits(64) for _ in range(31)]
        rn = r.choice([0, 3, 8, 19])
        regs[rn] = MEM
        pool = [i for i in range(29) if i != rn]
        rt, rt2 = r.sample(pool, 2)
        rs = r.choice([i for i in pool if i not in (rt, rt2)])
        sa, sb = r.sample(pool, 2)
        if r.random() < 0.15:
            sb = 31  # xzr
        lone = k % 10 == 9  # store without a prior load: must fail
        words = ([] if lone else [enc_ld(r.getrandbits(1), rt, rt2, rn)]) + [enc_st(r.getrandbits(1), rs, sa, sb, rn)]
        mem16 = bytes(r.getrandbits(8) for _ in range(16))
        cases.append((words, regs, mem16))
    work = os.path.join(ROOT, 'build', 'test_excl_pair')
    os.makedirs(work, exist_ok=True)
    src = ['#include <stdio.h>', '#include <stdlib.h>', '#include "cpu.h"', '#include "excl_pair.h"',
           'void fnprof_hit(uint64_t a, uint64_t l, uint64_t x) { (void)a; (void)l; (void)x; }',
           'void rt_dispatch(Cpu *c) { (void)c; abort(); }',
           'int main(void) { static unsigned char mem[16] __attribute__((aligned(16))); Cpu cc, *c = &cc;']
    for k, (words, regs, mem16) in enumerate(cases):
        src.append(f'  memset(c, 0, sizeof *c); c->excl_addr = ~0ull;')
        for i, v in enumerate(regs):
            src.append(f'  c->x[{i}] = {hex(v)}ull;')
        rn = (words[-1] >> 5) & 31
        src.append(f'  c->x[{rn}] = (uint64_t)(uintptr_t)mem;')
        src.append('  { static const unsigned char m0[16] = {' + ','.join(map(str, mem16)) + '}; memcpy(mem, m0, 16); }')
        for w in words:
            src.append('  ' + lift_excl_pair(w, 0).code)
        src.append(f'  c->x[{rn}] = {hex(MEM)}ull;')
        src.append(f'  printf("{k}"); for (int i = 0; i < 31; i++) printf(" %llx", (unsigned long long)c->x[i]);'
                   ' for (int i = 0; i < 16; i++) printf(" %02x", mem[i]); printf("\\n");')
    src.append('  return 0; }')
    cpath = os.path.join(work, 't.c')
    open(cpath, 'w').write('\n'.join(src))
    exe = os.path.join(work, 't.exe')
    cc = subprocess.run(['clang', '-O1', '-march=x86-64-v3', '-Wall', '-Wno-unused-function',
                         '-I', os.path.join(ROOT, 'runtime'), cpath, '-o', exe], capture_output=True, text=True)
    if cc.returncode or cc.stderr.strip():
        print('COMPILE (must be clean, no libatomic):\n' + cc.stderr[-3000:])
        sys.exit(1)
    run = subprocess.run([exe], capture_output=True, text=True)
    if run.returncode:
        print(f'test program exit {run.returncode}')
    lines = run.stdout.split('\n') + [''] * n
    bad = 0
    for k, (words, regs, mem16) in enumerate(cases):
        ur, um = unicorn_run(words, regs, mem16)
        want = f'{k} ' + ' '.join(f'{v:x}' for v in ur) + ' ' + ' '.join(f'{b:02x}' for b in um)
        if lines[k].strip() != want:
            bad += 1
            if bad <= 3:
                print(f'SEMANTICS case {k} words={[hex(w) for w in words]}\n  c   {lines[k]}\n  uni {want}')
    print(f'semantics vs unicorn: {n - bad}/{n} ok')
    fails += bad
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
