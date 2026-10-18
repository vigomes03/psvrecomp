"""Native positive/negative controls for an opt-in save-write interruption boundary."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CC = Path("D:/msys64/ucrt64/bin/clang.exe")


class SaveFaultTests(unittest.TestCase):
    def test_only_explicit_save_fault_exits(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "lab", prefix="save-fault-test-") as tmp:
            folder = Path(tmp)
            source = folder / "probe.c"
            source.write_text('#include "save_test_fault.h"\nint main(int argc, char **argv) {\n'
                              'save_test_after_write(argc > 1 && argv[1][0] == \'s\');\n'
                              'puts("returned"); return 0; }\n', encoding="utf-8")
            exe = folder / "probe.exe"
            env = dict(os.environ)
            env["PATH"] = str(CC.parent) + os.pathsep + env.get("PATH", "")
            build = subprocess.run([str(CC), "-std=c11", "-Wall", "-Werror", "-I",
                                    str(ROOT / "psvrecomp/runtime/platform"), str(source), "-o", str(exe)],
                                   env=env, capture_output=True, timeout=30)
            self.assertEqual(build.returncode, 0, build.stderr.decode(errors="replace"))
            for flag, kind, expected in [(None, "save", 0), ("0", "save", 0),
                                          ("1", "other", 0), ("1", "save", 86)]:
                with self.subTest(flag=flag, kind=kind):
                    child_env = dict(env)
                    child_env.pop("PVR_TEST_SAVE_AFTER_WRITE", None)
                    if flag is not None:
                        child_env["PVR_TEST_SAVE_AFTER_WRITE"] = flag
                    run = subprocess.run([str(exe), kind], env=child_env, capture_output=True, timeout=10)
                    self.assertEqual(run.returncode, expected, run.stderr)
                    if expected:
                        self.assertIn(b"[save-test] after write before Flush/Commit", run.stderr)
                        self.assertNotIn(b"returned", run.stdout)
                    else:
                        self.assertIn(b"returned", run.stdout)


if __name__ == "__main__":
    unittest.main()
