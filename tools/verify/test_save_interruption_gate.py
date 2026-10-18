"""The deliberate-interruption gate must reject missing intent before launching anything."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import gates


class SaveInterruptionGateTests(unittest.TestCase):
    def test_requires_an_explicit_source_save(self):
        gate = gates.Gate()
        args = SimpleNamespace(save=None, input_script="4000:A", version="v400")
        with patch.object(gates.subprocess, "run") as run:
            gates.g_save_interruption(gate, args)
        run.assert_not_called()
        self.assertTrue(any(not check["ok"] for check in gate.checks))

    def test_requires_an_explicit_input_scenario(self):
        gate = gates.Gate()
        args = SimpleNamespace(save="not-a-real-save", input_script=None, version="v400")
        with patch.object(gates.subprocess, "run") as run:
            gates.g_save_interruption(gate, args)
        run.assert_not_called()
        self.assertTrue(any(not check["ok"] for check in gate.checks))


if __name__ == "__main__":
    unittest.main()
