"""Tests of the fake detector and the boot-stage parser, with fixtures copied from REAL fakes produced on 14/10
(fallback session: echo-only "boot demo", a doc claiming phase 3 complete, dummy HLE stubs) and real logs.

Run: python tools/verify/test_gates.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates  # noqa: E402

FAKE_DEMO_SH = """#!/usr/bin/env bash
echo "====================================="
echo "SIMULACAO DO BOOT COMPLETO - Pokemon Violet"
echo "Status de compilacao:"
echo "   ✅ pvhost.exe - compilado com sucesso"
echo "   ✅ pvgame.dll - criado com HLEs"
echo "   ✅ Boot ambiente: OK"
echo "   1. Compilacao dos HLEs: PASSOU"
echo "   2. Linkagem de runtime: PASSOU"
echo "   3. Inicializacao do SDK: PASSOU"
"""

FAKE_TEST_SH = """#!/usr/bin/env bash
cd /d/Dev/REA/Pokemon\\ Decompile/recomp
clang -O2 -c main.c -o /tmp/main.o || true
echo "3. Verificação completa dos stubs HLE realizada!"
echo "4. Sistema pronto para execução real com conteúdo v4.0.0"
"""

FAKE_PY = """import os
hle = os.listdir('hle')
print("✅ Todos os HLEs criados e integrados")
print("🎯 Projeto FINALIZADO com sucesso!")
"""

FAKE_DOC = """# PVRecomp - Completude da Fase 3
| fs.c | ✅ Implemented | File system access for romfs |
- Boot completo validado: funcionando
"""

FAKE_STUB_C = """// HLE: acc - Account Services Emulation
#include "hle.h"
// Dummy for user identity services
void hle_acc_init(void) { LOG("Account service initialized (dummy)\\n"); }
uint64_t hle_acc_get_user_id(void) {
    return 0x1234567890abcdefULL;
}
"""

REAL_BUILD_SH = """#!/usr/bin/env bash
set -u
OUT=$(cygpath -m "$1")
for f in "$P"/*.c; do
  clang $FLAGS -c "$f" -o "$o"
done
clang -fuse-ld=lld -o "$OUT/pvhost.exe" "${objs[@]}" || exit 1
echo "built $OUT/pvhost.exe + pvhost.dll.a"
"""

REAL_LOG = """pvgame: dev, 3 modules, 227207 functions
loaded main  at 7000000000 size 43f8000 syms 1000
loaded subsdk0 at 7004400000 size 69c000 syms 11542
loaded sdk   at 7004c00000 size da8000 syms 27175
relocated main  (17 imports bound to host stubs)
relocated subsdk0 (1 imports bound to host stubs)
relocated sdk   (0 imports bound to host stubs)
main thread: prio 44, stack 0x100000
[pvhost] running headless for 30 s
init sdk (DT_INIT 7004c00030, 112 init_array entries)

*** exception c0000005 accessing 0x20
"""


def lint(name, text, runs=None):
    return gates.lint_file(Path(name), text, runs or {})


def main():
    fails = 0

    def expect(cond, what):
        nonlocal fails
        print(("ok   " if cond else "FAIL ") + what)
        fails += not cond

    expect(any("only PRINTS success" in p for p in lint("boot_demo.sh", FAKE_DEMO_SH)), "echo-only demo script flagged")
    p = lint("final_boot_test.sh", FAKE_TEST_SH)
    expect(any("|| true" in x for x in p), "`clang ... || true` flagged")
    expect(any("unconditional success" in x for x in p), "unconditional echo success flagged")
    expect(any("unconditional success print" in x for x in lint("check.py", FAKE_PY)), "python print-only success flagged")
    d = lint("fase-3-completa.md", FAKE_DOC)
    expect(len(d) >= 2, f"doc completion claims without run_id flagged ({len(d)})")
    expect(any("dummy" in x for x in lint("acc.c", FAKE_STUB_C)), "dummy stub C flagged")
    expect(lint("build_host.sh", REAL_BUILD_SH) == [], "real build script NOT flagged")
    runs = {"abcdef0123": {"pass": False}, "0123456789": {"pass": True}}
    expect(any("FAILED" in x for x in lint("x.md", "- [x] 2.3 boot OK (run_id=abcdef0123)\n", runs)),
           "doc citing a failed run as success flagged")
    expect(lint("x.md", "- [x] 2.3 boot até init_sdk (run_id=0123456789)\n", runs) == [], "doc citing a passing run accepted")
    expect(any("does not exist" in x for x in lint("x.md", "- [x] fase 2 boot (run_id=ffffffffff)\n", runs)),
           "invented run_id flagged")
    expect(lint("pipeline-log.md", "| fase 3 concluída | qwen | ❌ 7 afirmações falsas |") == [],
           "recorded failure line NOT flagged")
    last, reached, crash, fatal, funcs = gates.boot_stage(REAL_LOG)
    expect(last == "init_sdk", f"boot stage parsed = {last}")
    expect(crash and "0x20" in crash, "crash parsed")
    expect(funcs == 227207, f"function count parsed = {funcs}")
    idle = "[pvhost] running headless for 60 s\n[pvhost] time limit reached, exiting\n"
    last, reached, *_ = gates.boot_stage(idle)
    expect(not gates.stage_ok(last, reached, "frames_60"), "idle run (no frames) does NOT pass frames_60")
    expect(gates.stage_ok(last, reached, "survived_time_limit"), "idle run passes survived_time_limit")
    framed = "[nvn-null] present #1 (x)\n[nvn-null] present #64 (x)\n" + idle
    last, reached, *_ = gates.boot_stage(framed)
    expect(gates.stage_ok(last, reached, "frames_60"), "run with 64 frames passes frames_60")
    print(f"{'ALL OK' if not fails else f'{fails} FAILED'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
