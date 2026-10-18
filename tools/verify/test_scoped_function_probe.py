"""Real Ghidra controls for two explicitly bounded candidate functions."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis import build_probe_fixture as fixtures
from tools.analysis.ghidra_call_probe import CallProbeError

# A callable ABI-correct fixture, keeping BL at entry+4 like the existing builder.
ASSEMBLY = """\
.text
.global entry
entry:
    stp x29, x30, [sp, #-16]!
    bl callee
    ldp x29, x30, [sp], #16
    ret
callee:
    mov x0, #3
    ret
"""


class ScopedFunctionProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        module = ROOT / "tools/analysis/scoped_function_probe.py"
        if not module.is_file():
            raise AssertionError("Missing scoped two-function analysis entry")
        from tools.analysis.scoped_function_probe import run_scoped_probe
        cls.run_scoped = staticmethod(run_scoped_probe)
        cls.folder = ROOT / "lab/analysis-probe-tests" / ("scoped-" + uuid.uuid4().hex[:10])
        with patch.object(fixtures, "ASSEMBLY", ASSEMBLY):
            cls.fixture = fixtures.build_probe_fixture(cls.folder / "fixture")
        print("Retained scoped Ghidra controls:", cls.folder, flush=True)

    def run_case(self, label, site=None, callee=None):
        f = self.fixture
        return self.run_scoped(
            binary_path=f.bin_path, base_addr=f.base_addr,
            call_site_addr=f.call_site_addr if site is None else site,
            caller_start=f.entry_addr, caller_end=f.callee_addr - 1,
            callee_start=f.callee_addr if callee is None else callee,
            callee_end=f.base_addr + f.bin_path.stat().st_size - 1,
            work_dir=self.folder / label,
        )

    def test_real_decompiler_and_independent_target_with_explicit_function_bounds(self):
        result = self.run_case("positive")
        self.assertTrue(result["is_call"])
        self.assertEqual(int(result["target"], 16), self.fixture.callee_addr)
        self.assertEqual(result["function_count"], 2)
        self.assertEqual(result["function_provenance"], "supplied-symbol-intervals")
        self.assertTrue(result["auto_analysis_disabled"])
        self.assertTrue(result["caller_decompiled"])
        self.assertTrue(result["callee_decompiled"])
        caller = Path(result["caller_pseudocode"])
        callee = Path(result["callee_pseudocode"])
        self.assertTrue(caller.is_file())
        self.assertTrue(callee.is_file())
        self.assertIn("candidate_callee", caller.read_text(encoding="utf-8"))
        self.assertIn("return", callee.read_text(encoding="utf-8"))
        self.assertIn("3", callee.read_text(encoding="utf-8"))

    def test_an_unexpected_third_function_is_rejected_from_actual_engine_metadata(self):
        from tools.analysis import ghidra_call_probe
        folder = self.folder / "extra-function"
        with patch.object(fixtures, "ASSEMBLY", ASSEMBLY + "\nthird:\n    ret\n"):
            fixture = fixtures.build_probe_fixture(folder / "fixture")
        scripts = folder / "scripts"
        scripts.mkdir(parents=True)
        original = (ROOT / "tools/analysis/ScopedFunctionProbe.java").read_text(encoding="utf-8")
        marker = "        StringBuilder json = new StringBuilder();"
        self.assertEqual(original.count(marker), 1)
        # Inject an extra real database function after analysis, not a fake JSON result.
        mutation = ("        Address extra = calleeEnd.add(1);\n"
                    "        currentProgram.getFunctionManager().createFunction(\"unexpected\", extra,\n"
                    "            new AddressSet(extra, extra.add(3)), SourceType.USER_DEFINED);\n")
        (scripts / "ScopedFunctionProbe.java").write_text(
            original.replace(marker, mutation + marker), encoding="utf-8")
        with patch.object(ghidra_call_probe, "SCRIPT_DIR", scripts):
            with self.assertRaisesRegex(CallProbeError, "exactly 2 candidate"):
                self.run_scoped(
                    binary_path=fixture.bin_path, base_addr=fixture.base_addr,
                    call_site_addr=fixture.call_site_addr,
                    caller_start=fixture.entry_addr, caller_end=fixture.callee_addr - 1,
                    callee_start=fixture.callee_addr,
                    callee_end=fixture.base_addr + fixture.bin_path.stat().st_size - 5,
                    work_dir=folder / "run")

    def test_observed_interior_call_is_seeded_without_claiming_entry_reachability(self):
        folder = self.folder / "interior-site"
        assembly = ".text\n.global entry\nentry:\n    b done\n    bl callee\ndone:\n    ret\ncallee:\n    mov x0, #3\n    ret\n"
        with patch.object(fixtures, "ASSEMBLY", assembly):
            fixture = fixtures.build_probe_fixture(folder / "fixture")
        result = self.run_scoped(
            binary_path=fixture.bin_path, base_addr=fixture.base_addr,
            call_site_addr=fixture.call_site_addr,
            caller_start=fixture.entry_addr, caller_end=fixture.callee_addr - 1,
            callee_start=fixture.callee_addr,
            callee_end=fixture.base_addr + fixture.bin_path.stat().st_size - 1,
            work_dir=folder / "run")
        self.assertTrue(result["is_call"])
        self.assertEqual(int(result["target"], 16), fixture.callee_addr)
        self.assertFalse(result["entry_cfg_decoded_call_site"])
        self.assertTrue(result["call_site_explicitly_seeded"])

    def test_non_call_cannot_be_reported_as_a_function_relationship(self):
        with self.assertRaises(CallProbeError):
            self.run_case("non-call", site=self.fixture.non_call_addr)

    def test_wrong_expected_target_is_rejected(self):
        with self.assertRaises(CallProbeError):
            self.run_case("wrong-target", callee=self.fixture.callee_addr + 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
