"""Native Windows controls for crash context, including the production SEH filter."""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CC = Path("D:/msys64/ucrt64/bin/clang.exe")
PLATFORM = ROOT / "psvrecomp/runtime/platform"
HEADER = PLATFORM / "windows_fault_context.h"

SOURCE = r'''
#include <windows.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include "windows_fault_context.h"

void plat_crash_handler_install(void);
#ifdef PVR_TEST_EXPOSE_SEH
void test_invoke_filter(EXCEPTION_POINTERS *ep);
#endif
// Link-only boundaries for unrelated production functions. These must never run:
// the fixture does not reserve guest memory or request a runtime backtrace.
bool rt_fault_watch(uint64_t fa, uint64_t pc) {
    (void)fa; (void)pc;
    ExitProcess(93);
}
const char *rt_host_fn_name(uint64_t pc, uint64_t *offset) {
    (void)pc; (void)offset;
    ExitProcess(94);
}
// The real production filter terminates through this runtime boundary.
// This fixture intercepts termination, not the exception/context capture.
_Noreturn void rt_fault_report(const char *what, uint64_t fa, uint64_t pc, uint64_t lr) {
    (void)what; (void)fa; (void)pc;
    fprintf(stderr, "[fixture-terminal] lr=%016llx\n", (unsigned long long)lr);
    fflush(stderr);
    ExitProcess(86);
}

static volatile short sink;
int main(int argc, char **argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    if (argc != 2) return 2;
    if (!strcmp(argv[1], "format") || !strcmp(argv[1], "other")) {
        EXCEPTION_RECORD er = {0};
        CONTEXT ctx = {0};
        er.ExceptionCode = EXCEPTION_ACCESS_VIOLATION;
        ctx.Rax = UINT64_C(0x1122334455667788);
        ctx.Rip = UINT64_C(0x1020304050607080);
        if (!strcmp(argv[1], "other")) {
            er.ExceptionCode = EXCEPTION_ILLEGAL_INSTRUCTION;
            er.NumberParameters = 2;
            er.ExceptionInformation[0] = 1;
            er.ExceptionInformation[1] = 8;
        }
        pvr_print_windows_fault_context(stderr, &er, &ctx);
        return 0;
    }
    plat_crash_handler_install();
#ifdef PVR_TEST_EXPOSE_SEH
    if (!strcmp(argv[1], "unreadable-stack") || !strcmp(argv[1], "readable-stack") ||
        !strcmp(argv[1], "guard-stack") || !strcmp(argv[1], "cross-page-stack")) {
        EXCEPTION_RECORD er = {0};
        CONTEXT ctx = {0};
        er.ExceptionCode = EXCEPTION_ACCESS_VIOLATION;
        er.NumberParameters = 2;
        er.ExceptionInformation[1] = 8;
        ctx.Rip = (DWORD64)(uintptr_t)main;
        SYSTEM_INFO info;
        GetSystemInfo(&info);
        unsigned char *memory = VirtualAlloc(NULL, 2 * info.dwPageSize,
                                            MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
        if (!memory) return 90;
        ctx.Rsp = (DWORD64)(uintptr_t)memory;
        DWORD previous;
        if (!strcmp(argv[1], "readable-stack"))
            *(uint64_t *)memory = UINT64_C(0x1122334455667788);
        else if (!strcmp(argv[1], "unreadable-stack")) {
            if (!VirtualProtect(memory, info.dwPageSize, PAGE_NOACCESS, &previous)) return 92;
        } else if (!strcmp(argv[1], "guard-stack")) {
            if (!VirtualProtect(memory, info.dwPageSize,
                                PAGE_READWRITE | PAGE_GUARD, &previous)) return 92;
        } else {
            ctx.Rsp += info.dwPageSize - 4;
            if (!VirtualProtect(memory + info.dwPageSize, info.dwPageSize,
                                PAGE_NOACCESS, &previous)) return 92;
        }
        EXCEPTION_POINTERS ep = {&er, &ctx};
        test_invoke_filter(&ep);
        return 91;
    }
#endif
    if (!strcmp(argv[1], "normal")) return 0;
    if (!strcmp(argv[1], "read")) sink = *(volatile short *)(uintptr_t)8;
    else if (!strcmp(argv[1], "write")) *(volatile short *)(uintptr_t)8 = 7;
    else if (!strcmp(argv[1], "execute")) ((void (*)(void))(uintptr_t)8)();
    else return 2;
    return 3;
}
'''


class WindowsFaultContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HEADER.is_file():
            raise AssertionError("Missing native-context diagnostic header")
        cls.tmp = tempfile.TemporaryDirectory(dir=ROOT / "lab", prefix="windows-fault-context-")
        cls.addClassCleanup(cls.tmp.cleanup)
        folder = Path(cls.tmp.name)
        source = folder / "probe.c"
        source.write_text(SOURCE, encoding="utf-8")
        cls.exe = folder / "probe.exe"
        cls.env = dict(os.environ)
        cls.env["PATH"] = str(CC.parent) + os.pathsep + cls.env.get("PATH", "")
        scratch = os.environ.get("TMPDIR", str(folder))
        cls.env.update(TMP=scratch, TEMP=scratch)
        cmd = [str(CC), "-std=c11", "-O0", "-ffunction-sections", "-fdata-sections",
               "-fuse-ld=lld", "-Wl,--gc-sections", "-I", str(PLATFORM),
               str(source), str(PLATFORM / "windows.c"), "-o", str(cls.exe),
               "-lwinmm", "-lole32", "-lshell32", "-ldbghelp", "-lbcrypt", "-lgdi32"]
        cls.compile_command = cmd
        cls.folder = folder
        result = subprocess.run(cmd, env=cls.env, capture_output=True, timeout=45)
        if result.returncode:
            raise AssertionError(result.stderr.decode(errors="replace"))

    def run_probe(self, mode):
        return subprocess.run([str(self.exe), mode], env=self.env,
                              capture_output=True, text=True, errors="replace", timeout=10)

    def test_format_preserves_64_bit_registers_and_missing_parameter_validity(self):
        result = self.run_probe("format")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("access=unknown", result.stderr)
        self.assertIn("valid=0", result.stderr)
        self.assertIn("rax=1122334455667788", result.stderr)
        self.assertIn("rip=1020304050607080", result.stderr)

    def test_non_memory_exception_parameters_are_not_an_access_violation(self):
        result = self.run_probe("other")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("access=unknown", result.stderr)
        self.assertIn("valid=0", result.stderr)

    def test_normal_production_handler_install_has_no_diagnostic_output(self):
        result = self.run_probe("normal")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[host-context]", result.stderr)
        self.assertNotIn("[fixture-terminal]", result.stderr)

    def test_removing_only_the_production_hook_removes_context_from_real_fault(self):
        hook = "    pvr_print_windows_fault_context(stderr, er, ep->ContextRecord);"
        original = (PLATFORM / "windows.c").read_text(encoding="utf-8")
        self.assertEqual(original.count(hook), 1)
        mutant_source = self.folder / "without_hook.c"
        mutant_source.write_text(original.replace(hook, "", 1), encoding="utf-8")
        mutant_exe = self.folder / "without_hook.exe"
        command = list(self.compile_command)
        command[command.index(str(PLATFORM / "windows.c"))] = str(mutant_source)
        command[command.index(str(self.exe))] = str(mutant_exe)
        built = subprocess.run(command, env=self.env, capture_output=True, timeout=45)
        self.assertEqual(built.returncode, 0, built.stderr.decode(errors="replace"))
        # Header remains available; only the production integration is absent.
        formatted = subprocess.run([str(mutant_exe), "format"], env=self.env,
                                   capture_output=True, text=True, errors="replace", timeout=10)
        self.assertEqual(formatted.returncode, 0, formatted.stderr)
        self.assertIn("[host-context]", formatted.stderr)
        fault = subprocess.run([str(mutant_exe), "read"], env=self.env,
                               capture_output=True, text=True, errors="replace", timeout=10)
        self.assertEqual(fault.returncode, 86, fault.stderr)
        self.assertIn("[fixture-terminal]", fault.stderr)
        self.assertNotIn("[host-context]", fault.stderr)

    def test_production_filter_does_not_fault_again_on_unreadable_saved_stack(self):
        exposed = self.folder / "exposed_filter.c"
        original = (PLATFORM / "windows.c").read_text(encoding="utf-8")
        exposed.write_text(original + "\nvoid test_invoke_filter(EXCEPTION_POINTERS *ep) {"
                           " (void)unhandled_filter(ep); }\n", encoding="utf-8")
        exe = self.folder / "unreadable_stack.exe"
        command = list(self.compile_command)
        command[command.index(str(PLATFORM / "windows.c"))] = str(exposed)
        command[command.index(str(self.exe))] = str(exe)
        command.append("-DPVR_TEST_EXPOSE_SEH")
        built = subprocess.run(command, env=self.env, capture_output=True, timeout=45)
        self.assertEqual(built.returncode, 0, built.stderr.decode(errors="replace"))
        for mode in ("unreadable-stack", "readable-stack", "guard-stack", "cross-page-stack"):
            with self.subTest(mode=mode):
                result = subprocess.run([str(exe), mode], env=self.env,
                                        capture_output=True, text=True, errors="replace", timeout=10)
                self.assertEqual(result.returncode, 86, result.stderr)
                self.assertEqual(result.stderr.count("[host-context] code="), 1, result.stderr)
                expected = "1122334455667788" if mode == "readable-stack" else "0000000000000000"
                self.assertIn("[fixture-terminal] lr=" + expected, result.stderr)

    def test_production_filter_captures_real_read_write_execute_faults(self):
        registers = ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp", "rip"]
        registers += ["r" + str(i) for i in range(8, 16)]
        for mode in ("read", "write", "execute"):
            with self.subTest(mode=mode):
                result = self.run_probe(mode)
                self.assertEqual(result.returncode, 86, result.stderr)
                self.assertIn("[fixture-terminal]", result.stderr)
                self.assertIn("access=" + mode, result.stderr)
                self.assertIn("valid=1", result.stderr)
                self.assertIn("address=0000000000000008", result.stderr)
                values = dict(re.findall(r"\b([a-z][a-z0-9]*)=([0-9a-f]{16})\b", result.stderr))
                for register in registers:
                    self.assertIn(register, values, result.stderr)
                self.assertNotEqual(int(values["rip"], 16), 0)
                self.assertNotEqual(int(values["rsp"], 16), 0)
                self.assertLess(result.stderr.index("[host-context]"),
                                result.stderr.index("[fixture-terminal]"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
