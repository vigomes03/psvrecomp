"""NSO verifier regression tests using only synthetic uncompressed segments."""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "psvrecomp/recomp/venv/Scripts/python.exe"
VERIFY = ROOT / "psvrecomp/recomp/nso_verify.py"


class NsoVerifyTests(unittest.TestCase):
    def run_verifier(self, corrupt=False, no_inputs=False):
        parent = ROOT / "lab" / "shortcut-tests"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            path = Path(tmp) / "main"
            header = bytearray(0x100)
            header[:4] = b"NSO0"
            data = bytearray()
            for i, offset in enumerate((0x10, 0x20, 0x30)):
                raw = bytes([i + 1]) * 16
                struct.pack_into("<III", header, offset, 0x100 + len(data), i * 0x1000, len(raw))
                struct.pack_into("<I", header, 0x60 + 4 * i, len(raw))
                header[0xA0 + i * 32:0xC0 + i * 32] = hashlib.sha256(raw).digest()
                data.extend(raw)
            if corrupt:
                data[0] ^= 1
            path.write_bytes(header + data)
            return subprocess.run([str(PYTHON), str(VERIFY)] + ([] if no_inputs else [str(path)]),
                                  capture_output=True, text=True, timeout=30)

    def test_valid_synthetic_segments(self):
        result = self.run_verifier()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("BAD", result.stdout)

    def test_hash_mismatch_is_a_failure(self):
        result = self.run_verifier(corrupt=True)
        self.assertIn("BAD", result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_empty_input_list_is_a_failure(self):
        self.assertNotEqual(self.run_verifier(no_inputs=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
