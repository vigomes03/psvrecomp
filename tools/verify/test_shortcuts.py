"""Exercise relocated CMD wrappers on disposable fixtures, never real extraction/builds.

Run on Windows: python tools/verify/test_shortcuts.py -v
Only the help path is initially exercised. Later cases use explicit failing fixture
commands to test wrapper flow; they are not evidence of a real game build or dump.
"""
import hashlib
import os
from pathlib import Path
import struct
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = (
    "extract_base.cmd", "extract_update_v400.cmd", "recompile_v400.cmd",
    "build_and_test_v400.cmd", "launch_game.cmd",
)


@unittest.skipUnless(os.name == "nt", "CMD wrappers require Windows")
class ShortcutTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / "lab" / "shortcut-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="wrapper fixture ", dir=parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "unrelated cwd").mkdir()
        for name in SCRIPTS:
            shutil.copyfile(ROOT / "scripts" / name, self.root / "scripts" / name)

    def cmd(self, command, input_text="", env=None):
        return subprocess.run(
            subprocess.list2cmdline([os.environ.get("COMSPEC", "cmd.exe")])
            + " /d /c " + command,
            cwd=self.root / "unrelated cwd", input=input_text,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30, env=env,
        )

    def fixture_engine(self, name):
        engine = self.root / "fixture-engine.cmd"
        engine.write_text("@echo off\necho FIXTURE_ENGINE_CALLED\nexit /b 7\n")
        script = self.root / "scripts" / name
        text = script.read_text(encoding="utf-8")
        text = text.replace('set "BASH=D:\\msys64\\usr\\bin\\bash.exe"',
                            f'set "BASH={engine}"')
        script.write_text(text, encoding="utf-8")
        return script

    def compile_inputs(self):
        (self.root / "dumps/v400/exefs").mkdir(parents=True)
        python = self.root / "psvrecomp/recomp/venv/Scripts/python.exe"
        python.parent.mkdir(parents=True)
        python.touch()  # Existence guard only; this fixture is never executed.

    def test_recompile_accepts_y_after_reading_the_prompt(self):
        self.compile_inputs()
        script = self.fixture_engine("recompile_v400.cmd")
        env = os.environ.copy()
        env.pop("ANSWER", None)
        result = self.cmd(f'call "{script}"', "Y\n", env)
        self.assertIn("FIXTURE_ENGINE_CALLED", result.stdout, result.stdout + result.stderr)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("recompilation failed", result.stdout)

    def test_recompile_declines_even_if_answer_was_inherited(self):
        self.compile_inputs()
        script = self.fixture_engine("recompile_v400.cmd")
        env = os.environ.copy()
        env["ANSWER"] = "Y"
        result = self.cmd(f'call "{script}"', "N\n", env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Cancelled.", result.stdout)
        self.assertNotIn("FIXTURE_ENGINE_CALLED", result.stdout)

    def test_build_refuses_a_running_game_without_calling_engine(self):
        script = self.fixture_engine("build_and_test_v400.cmd")
        for name in ("obj", "obj_sdk", "obj_subsdk0"):
            (self.root / "lab/gen-v400" / name).mkdir(parents=True)
        tasklist = self.root / "tasklist.cmd"
        tasklist.write_text("@echo off\necho pvhost.exe 123 Console\nexit /b 0\n")
        env = os.environ.copy()
        env["PATH"] = str(self.root) + os.pathsep + env["PATH"]
        result = self.cmd(f'call "{script}"', env=env)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("already running", result.stdout)
        self.assertNotIn("FIXTURE_ENGINE_CALLED", result.stdout)

    def test_extraction_recognizes_utf8_rom_names_from_legacy_console(self):
        self.compile_inputs()
        (self.root / "roms").mkdir()
        names = {"extract_base.cmd": "Pokémon Violet.xci",
                 "extract_update_v400.cmd": "Pokémon Violet Update V4.0.0.nsp"}
        for script, filename in names.items():
            with self.subTest(script=script):
                (self.root / "roms" / filename).touch()  # Empty fixture, never extracted.
                result = self.cmd(f'chcp 437 >nul & call "{self.root / "scripts" / script}"')
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("keys not found", result.stdout, result.stdout + result.stderr)

    def test_launch_forwards_quoted_arguments_and_exit_status(self):
        target = self.root / "psvrecomp/recomp/run_window.cmd"
        target.parent.mkdir(parents=True)
        target.write_text('@echo off\necho HOST=%~1\necho VERSION=%~2\nexit /b 13\n')
        result = self.cmd(f'call "{self.root / "scripts/launch_game.cmd"}" "host with spaces" v400')
        self.assertEqual(result.returncode, 13, result.stdout + result.stderr)
        self.assertIn("HOST=host with spaces", result.stdout)
        self.assertIn("VERSION=v400", result.stdout)

    def test_update_validation_stage_checks_extensionless_modules(self):
        # Run the actual verification block, not the extraction/key-handling stages.
        folder = self.root / "dumps/v400/exefs"
        folder.mkdir(parents=True)
        header = bytearray(0x100)
        header[:4] = b"NSO0"
        data = bytearray()
        for i, offset in enumerate((0x10, 0x20, 0x30)):
            raw = bytes([i + 1]) * 16
            struct.pack_into("<III", header, offset, 0x100 + len(data), i * 0x1000, len(raw))
            struct.pack_into("<I", header, 0x60 + i * 4, len(raw))
            header[0xA0 + i * 32:0xC0 + i * 32] = hashlib.sha256(raw).digest()
            data.extend(raw)
        for module in ("main", "sdk", "subsdk0"):
            (folder / module).write_bytes(header + data)
        verifier = self.root / "psvrecomp/recomp/nso_verify.py"
        verifier.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / "psvrecomp/recomp/nso_verify.py", verifier)
        text = (self.root / "scripts/extract_update_v400.cmd").read_text(encoding="utf-8")
        block = text[text.index("echo [4/4]"):text.index("\n:help\n")]
        stage = self.root / "scripts/verify-stage.cmd"
        stage.write_text('@echo off\nsetlocal\ncd /d "%~dp0.."\n'
                         f'set "PYTHON={ROOT / "psvrecomp/recomp/venv/Scripts/python.exe"}"\n'
                         'set "V400=dumps\\v400"\nset "UPDATEOUT=fixture"\n'
                         f'set "LOG={self.root / "fixture.log"}"\n' + block, encoding="utf-8")
        result = self.cmd(f'call "{stage}"')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for module in ("main", "sdk", "subsdk0"):
            self.assertIn(module, result.stdout)
        bad = bytearray(header + data)
        bad[-1] ^= 1
        (folder / "sdk").write_bytes(bad)
        result = self.cmd(f'call "{stage}"')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("BAD", result.stdout)
        self.assertNotIn("Complete:", result.stdout)
        (folder / "main").unlink()
        result = self.cmd(f'call "{stage}"')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("NSO verification failed", result.stdout)

    def test_help_resolves_project_root_from_an_unrelated_cwd(self):
        for name in SCRIPTS:
            with self.subTest(script=name):
                script = self.root / "scripts" / name
                # Probe CWD inside the help branch: SETLOCAL restores it on return.
                text = script.read_text(encoding="utf-8")
                script.write_text(text.replace(":help\n", ":help\ncd\n"), encoding="utf-8")
                result = self.cmd(f'call "{script}" --help')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("Usage:", result.stdout)
                self.assertEqual(result.stdout.strip().splitlines()[0].casefold(),
                                 str(self.root).casefold())
                self.assertFalse(result.stderr.strip(), result.stderr)


if __name__ == "__main__":
    unittest.main()
