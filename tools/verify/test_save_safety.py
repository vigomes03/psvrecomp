"""Save-copy safety tests on disposable synthetic data, never the player's save."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import gates


class SaveIsolationTests(unittest.TestCase):
    def setUp(self):
        parent = gates.ROOT / "lab" / "save-isolation-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.seed = self.root / "seed"
        (self.seed / "save_0").mkdir(parents=True)
        (self.seed / "save_0/main").write_bytes(b"synthetic-save" * 50)
        self.target = self.root / "sandbox"

    def test_same_source_and_target_is_rejected_before_deletion(self):
        with self.assertRaises(ValueError):
            gates.prepare_window_save(self.seed, self.seed)
        self.assertTrue((self.seed / "save_0/main").exists())

    def test_related_paths_are_rejected(self):
        for source, target in ((self.seed, self.seed / "child"), (self.seed, self.root)):
            with self.subTest(source=source, target=target), self.assertRaises(ValueError):
                gates.prepare_window_save(source, target)
        self.assertTrue((self.seed / "save_0/main").exists())

    def test_missing_source_preserves_existing_sandbox(self):
        self.target.mkdir()
        marker = self.target / "keep"
        marker.write_text("keep")
        with self.assertRaises(ValueError):
            gates.prepare_window_save(self.root / "missing", self.target)
        self.assertTrue(marker.exists())

    def test_interrupted_copy_session_recovers_from_untouched_seed(self):
        before = gates.save_manifest(self.seed)
        gates.prepare_window_save(self.seed, self.target)
        self.assertEqual(before, gates.save_manifest(self.target))
        # Simulate a process dying mid-write to EXPENDABLE data, not game atomicity.
        script = "import os,sys; f=open(sys.argv[1],'wb'); f.write(b'partial'); f.flush(); os.fsync(f.fileno()); os._exit(23)"
        result = subprocess.run([sys.executable, "-c", script, str(self.target / "save_0/main")], timeout=20)
        self.assertEqual(result.returncode, 23)
        self.assertNotEqual(before, gates.save_manifest(self.target))
        self.assertEqual(before, gates.save_manifest(self.seed))
        gates.prepare_window_save(self.seed, self.target)
        self.assertEqual(before, gates.save_manifest(self.target))


if __name__ == "__main__":
    unittest.main()
