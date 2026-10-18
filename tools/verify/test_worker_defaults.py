"""Project worker selection: verify the actual argparse defaults without loading a model."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKERS = ("tools/workers/local_worker.py", "tools/workers/translate_worker.py", "tools/rea/rea_worker.py")


class WorkerDefaultsTests(unittest.TestCase):
    def test_project_workers_default_to_qwen(self):
        for filename in WORKERS:
            with self.subTest(worker=filename):
                tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
                calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument"
                         and any(isinstance(a, ast.Constant) and a.value == "--model" for a in n.args)]
                self.assertEqual(len(calls), 1)
                default = next(k.value for k in calls[0].keywords if k.arg == "default")
                self.assertEqual(ast.literal_eval(default), "qwen3.8:27b")


if __name__ == "__main__":
    unittest.main()
