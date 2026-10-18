"""Real installed-Ghidra controls on our clang-assembled synthetic ARM64 fixture."""
from pathlib import Path
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.build_probe_fixture import build_probe_fixture
from tools.analysis.ghidra_call_probe import CallProbeError, LANGUAGE_ID, run_call_probe


class GhidraCallProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / "lab" / "analysis-probe-tests" / ("controls-" + uuid.uuid4().hex[:10])
        cls.fixture = build_probe_fixture(cls.output / "fixture")
        print("Retained real-Ghidra controls:", cls.output, flush=True)

    def test_known_call_resolves_to_expected_callee(self):
        fixture = self.fixture
        result = run_call_probe(fixture.bin_path, fixture.base_addr,
                                fixture.call_site_addr, self.output / "positive")
        self.assertEqual(result.language, LANGUAGE_ID)
        self.assertEqual(result.image_base, fixture.base_addr)
        self.assertEqual(result.call_site, fixture.call_site_addr)
        self.assertTrue(result.instruction_present)
        self.assertTrue(result.is_call)
        self.assertEqual(result.mnemonic.lower(), "bl")
        self.assertEqual(result.target, fixture.callee_addr)
        self.assertIsInstance(result.target_function, str)
        self.assertTrue(result.target_function)


    def test_non_call_is_not_a_call_relationship(self):
        fixture = self.fixture
        result = run_call_probe(fixture.bin_path, fixture.base_addr,
                                fixture.non_call_addr, self.output / "negative")
        self.assertTrue(result.instruction_present)
        self.assertFalse(result.is_call)
        self.assertNotEqual(result.mnemonic.lower(), "bl")
        self.assertIsNone(result.target)
        self.assertIsNone(result.target_function)

    def test_missing_post_script_is_not_accepted_as_import_success(self):
        from unittest.mock import patch
        from tools.analysis import ghidra_call_probe
        fixture = self.fixture
        # Fault only the script-name argument; the installed Ghidra still runs.
        with patch.object(ghidra_call_probe, "SCRIPT_NAME", "MissingProbeControl.java"):
            with self.assertRaisesRegex(CallProbeError, "no output JSON|exited with code"):
                run_call_probe(fixture.bin_path, fixture.base_addr,
                               fixture.call_site_addr, self.output / "missing-script")

    def test_missing_input_fails_before_creating_outputs(self):
        folder = self.output / "missing-input"
        with self.assertRaises(CallProbeError):
            run_call_probe(self.output / "not-present.bin", self.fixture.base_addr,
                           self.fixture.call_site_addr, folder)
        self.assertFalse(folder.exists())

    def test_timeout_reaps_its_owned_java_process(self):
        import psutil
        import time
        fixture = self.fixture
        folder = self.output / "timeout"
        marker = str(folder).replace("\\", "/").lower()
        def owned_java():
            found = []
            for process in psutil.process_iter(["pid", "name", "cmdline"]):
                command = " ".join(process.info["cmdline"] or []).replace("\\", "/").lower()
                if (process.info["name"] or "").lower() == "java.exe" and marker in command:
                    found.append(process)
            return found
        try:
            started = time.monotonic()
            with self.assertRaisesRegex(CallProbeError, "timed out"):
                run_call_probe(fixture.bin_path, fixture.base_addr,
                               fixture.call_site_addr, folder, timeout_s=0.5)
            elapsed = time.monotonic() - started
            print("Timeout control elapsed:", round(elapsed, 3), flush=True)
            self.assertLess(elapsed, 2.0, "Timeout waited for the JVM to finish normally")
            self.assertEqual([p.pid for p in owned_java()], [], "Own JVM survived timeout")
        finally:
            # A failing regression must not leave its intentionally timed-out JVM alive.
            for process in owned_java():
                try:
                    process.kill()
                    process.wait(timeout=10)
                except psutil.NoSuchProcess:
                    pass

    def test_unaligned_address_is_rejected(self):
        fixture = self.fixture
        with self.assertRaises(CallProbeError):
            run_call_probe(fixture.bin_path, fixture.base_addr,
                           fixture.call_site_addr + 1, self.output / "unaligned")


if __name__ == "__main__":
    unittest.main(verbosity=2)
