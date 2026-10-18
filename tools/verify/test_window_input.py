"""Window gates use deliberate input without inheriting a user's debug settings."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import gates


class WindowInputTests(unittest.TestCase):
    def test_default_removes_ambient_input_and_fps_overrides(self):
        with patch.dict(gates.os.environ, {"PVR_INPUT": "ambient", "PVR_GAME60": "1", "PVR_TEST_SAVE_AFTER_WRITE": "1", "SAVE_SEED": "original",
                                          "LARECOMP_SETTINGS": "manual.ini"}):
            env = gates.window_environment(gates.LAB / "host-vk-auto", gates.LAB / "host-vk-auto/save_gate")
        for key in ("PVR_INPUT", "PVR_GAME60", "PVR_TEST_SAVE_AFTER_WRITE", "SAVE_SEED"):
            self.assertFalse(key in env, f"ambient {key} leaked into window environment")
        self.assertEqual(env["LARECOMP_SETTINGS"], "build/psvrecomp_auto.ini")

    def test_explicit_script_disables_periodic_default_button_press(self):
        host = gates.LAB / "host-vk-auto"
        script = "12000:X,15000:R,18000:A,21000:A,24000:B"
        env = gates.window_environment(host, host / "save_gate", script)
        self.assertEqual(env["PVR_INPUT"], script)
        self.assertEqual(env["PVR_AUTOPRESS"], "A:1000000:100:999999")
        self.assertEqual(env["PVR_HOST_DIR"], gates.bpath(host))


if __name__ == "__main__":
    unittest.main()
