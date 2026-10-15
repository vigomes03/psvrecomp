"""Oracle for tools/rea/glsl_slice.py (card W20). Run: python tools/verify/test_glsl_slice.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(HERE, '..', 'rea', 'glsl_slice.py')

FIXTURE = """void main() {
  uint r1 = 0u;
  switch (pc) {
  case 0u:
    // pc 0: 4c98078c00170001
    r1 = cb3[1][0];
  case 8u:
    // pc 8: 3868103f00070102
    r2 = as_u((as_f(r1) * as_f(0x3f000000u)));
  case 16u:
    // pc 10: 5c9807800ff00003
  if (p0) {
    r3 = 0u;
  }
  case 24u:
    // pc 18: da40040ff0370203
    { vec4 t = texture(t0, vec2(as_f(r2), as_f(r5)));
      r3 = as_u(t[0]);
      r4 = as_u(t[1]);
    }
  case 32u:
    // pc 20: 5c58100000470306
  if (p1) {
    r7 = as_u((as_f(r4) * as_f(r4)));
  }
  case 40u:
    // pc 28: 5c58100000470306
    r6 = as_u((as_f(r3) + as_f(r4) + as_f(r7)));
  case 48u:
    // pc 30: e30000000007000f
    exit_now = true; break;
  }
}
"""

# (reg, pc) pairs the slice from pc 28 / r6 must contain, and nothing else.
# r7 at pc 20 is predicated (p1): the walk continues past it, finds no earlier def -> r7 "undefined" entry.
# r3 at pc 18 is unconditional: the predicated r3 at pc 10 must NOT appear.
EXPECTED = {
    ('r6', '28'), ('r3', '18'), ('r4', '18'), ('r7', '20'), ('r2', '8'), ('r1', '0'),
    ('r5', None), ('r7', None),
}
EXPECTED_PRED = {('r7', '20'): 'p1'}
EXPECTED_USES = {('r6', '28'): ['r3', 'r4', 'r7'], ('r3', '18'): ['r2', 'r5'], ('r1', '0'): []}


def main():
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, 'fix_fs.glsl')
        open(src, 'w', newline='\n').write(FIXTURE)
        p = subprocess.run([sys.executable, SLICE, src, '--pc', '28', '--reg', 'r6'], capture_output=True, text=True)
        if p.returncode != 0:
            print('FAIL: exit', p.returncode, p.stderr[-800:]); return 1
        rows = [json.loads(l) for l in p.stdout.splitlines() if l.strip()]
        got = {(r['reg'], r['pc']) for r in rows}
        ok = True
        if got != EXPECTED:
            print('FAIL set: missing', EXPECTED - got, 'extra', got - EXPECTED); ok = False
        for r in rows:
            k = (r['reg'], r['pc'])
            if k in EXPECTED_PRED and r.get('pred') != EXPECTED_PRED[k]:
                print('FAIL pred', k, r.get('pred')); ok = False
            if k[1] is not None and k not in EXPECTED_PRED and r.get('pred') is not None:
                print('FAIL pred should be null', k, r.get('pred')); ok = False
            if k in EXPECTED_USES and sorted(r.get('uses', [])) != EXPECTED_USES[k]:
                print('FAIL uses', k, r.get('uses')); ok = False
            if k[1] is not None and not isinstance(r.get('line'), int):
                print('FAIL line', k, r.get('line')); ok = False
        # real file smoke test (lab, optional): must not crash
        real = os.path.join(HERE, '..', '..', 'lab', 'host-vk', 'glsl_hair', '74421cd200_fs.glsl')
        if os.path.exists(real):
            q = subprocess.run([sys.executable, SLICE, real, '--pc', '3568', '--reg', 'r10', '--depth', '3'],
                               capture_output=True, text=True)
            if q.returncode != 0 or not q.stdout.strip():
                print('FAIL real file', q.returncode, q.stderr[-500:]); ok = False
        print('PASS' if ok else 'FAIL')
        return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
