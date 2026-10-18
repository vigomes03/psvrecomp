"""Reject gameplay evidence produced by a runtime built from stale sources."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import gates


class RuntimeFreshnessTests(unittest.TestCase):
    def setUp(self):
        parent = gates.ROOT / "lab" / "freshness-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.tmp.cleanup)
        self.host = Path(self.tmp.name)
        exe = self.host / "pvhost.exe"
        exe.write_bytes(b"synthetic-unit-test-image-not-a-host")
        self.key = gates.mpath(exe.relative_to(gates.ROOT))
        self.record = {"run_id": "unit-fixture", "gate": "host", "pass": True,
                       "info": {"backend": "vulkan", "runtime_sources": {"runtime/fs.c": "old"}},
                       "artifacts": {self.key: {"sha256": gates.sha256(exe)}}}

    def test_matching_binary_but_changed_source_is_rejected(self):
        with patch.object(gates, "runtime_source_manifest", return_value={"runtime/fs.c": "new"}):
            self.assertIsNone(gates.host_build_provenance(self.host, [self.record]))

    def test_matching_source_and_binary_is_accepted(self):
        with patch.object(gates, "runtime_source_manifest", return_value={"runtime/fs.c": "old"}):
            self.assertEqual(gates.host_build_provenance(self.host, [self.record]), "unit-fixture")

    def test_headless_build_cannot_validate_vulkan(self):
        self.record["info"]["backend"] = "null"
        with patch.object(gates, "runtime_source_manifest", return_value={"runtime/fs.c": "old"}):
            self.assertIsNone(gates.host_build_provenance(self.host, [self.record]))

    def test_changed_binary_is_rejected(self):
        (self.host / "pvhost.exe").write_bytes(b"different-unit-fixture")
        with patch.object(gates, "runtime_source_manifest", return_value={"runtime/fs.c": "old"}):
            self.assertIsNone(gates.host_build_provenance(self.host, [self.record]))


if __name__ == "__main__":
    unittest.main()
