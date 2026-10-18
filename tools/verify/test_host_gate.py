"""Host-gate command routing tests; no compiler or game is invoked here."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import gates


class HostRoutingTests(unittest.TestCase):
    def check_backend(self, backend, expected_folder):
        parent = gates.ROOT / "lab" / "gate-routing-tests"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            gate = gates.Gate()
            with patch.object(gates, "LAB", Path(tmp)), patch.object(gates, "sh", return_value=(0, "")) as shell:
                gates.g_host(gate, SimpleNamespace(version="v400", backend=backend))
            command = shell.call_args.args[0]
            self.assertIn(expected_folder, command)
            self.assertTrue(command.endswith('" ' + backend), command)
            self.assertEqual(gate.info["backend"], backend)
            # This unit test creates no output binaries and must not assert a real build.
            self.assertTrue(any(not c["ok"] for c in gate.checks))

    def test_null_backend_keeps_versioned_headless_host(self):
        self.check_backend("null", "host-v400")

    def test_vulkan_link_uses_window_host(self):
        parent = gates.ROOT / "lab" / "gate-routing-tests"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            gate = gates.Gate()
            with patch.object(gates, "LAB", Path(tmp)), patch.object(gates, "sh", return_value=(1, "fixture failure")) as shell:
                gates.g_link(gate, SimpleNamespace(version="v400", backend="vulkan"))
            self.assertIn("host-vk-auto", shell.call_args.args[0])
            self.assertTrue(any(not c["ok"] for c in gate.checks))

    def test_vulkan_backend_uses_window_host(self):
        self.check_backend("vulkan", "host-vk-auto")


if __name__ == "__main__":
    unittest.main()
