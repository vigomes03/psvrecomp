"""Native OCR positive control, using synthetic text rather than a game screenshot."""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.name == "nt", "Windows OCR integration")
class WindowsOcrTests(unittest.TestCase):
    def test_recognizes_synthetic_save_label(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "lab", prefix="ocr-fixture-") as tmp:
            image = Path(tmp) / "synthetic.png"
            quoted = str(image).replace("'", "''")
            make_image = (
                "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Drawing; "
                "$b=New-Object System.Drawing.Bitmap(700,180); "
                "$g=[System.Drawing.Graphics]::FromImage($b); $g.Clear([System.Drawing.Color]::Black); "
                "$f=New-Object System.Drawing.Font('Arial',48); "
                "$g.DrawString('SAVE 1234',$f,[System.Drawing.Brushes]::White,20,30); "
                f"$b.Save('{quoted}',[System.Drawing.Imaging.ImageFormat]::Png); "
                "$g.Dispose();$f.Dispose();$b.Dispose()"
            )
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", make_image], check=True,
                           capture_output=True, timeout=30)
            result = subprocess.run(["powershell.exe", "-NoProfile", "-File",
                                     str(ROOT / "tools/verify/windows_ocr.ps1"), "-ImagePath", str(image)],
                                    capture_output=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
            output = json.loads(result.stdout)
            self.assertEqual("".join(output["text"].upper().split()), "SAVE1234")
            self.assertTrue(output["language"])


if __name__ == "__main__":
    unittest.main()
