import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from unslothkit.data import check_data, convert_csv_to_jsonl, split_jsonl
from unslothkit.recommend import recommend_models
from unslothkit.templates import create_project


class DataTests(unittest.TestCase):
    def test_good_chat_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "train.jsonl"
            p.write_text(json.dumps({"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]}) + "\n")
            report = check_data(p)
            self.assertTrue(report.ok)
            self.assertEqual(report.total_examples, 1)

    def test_missing_assistant_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "train.jsonl"
            p.write_text(json.dumps({"messages": [{"role": "user", "content": "hi"}]}) + "\n")
            report = check_data(p)
            self.assertFalse(report.ok)
            self.assertTrue(any("assistant" in i.message for i in report.errors))

    def test_convert_csv(self):
        with tempfile.TemporaryDirectory() as td:
            csvp = Path(td) / "data.csv"
            out = Path(td) / "data.jsonl"
            csvp.write_text("instruction,output\nSay hi,Hello\n")
            n = convert_csv_to_jsonl(csvp, out)
            self.assertEqual(n, 1)
            self.assertTrue(check_data(out).ok)

    def test_split_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "all.jsonl"
            rows = [json.dumps({"messages": [{"role": "user", "content": f"q{i}"}, {"role": "assistant", "content": f"a{i}"}]}) for i in range(10)]
            src.write_text("\n".join(rows) + "\n")
            train = Path(td) / "train.jsonl"
            ev = Path(td) / "eval.jsonl"
            train_n, eval_n = split_jsonl(src, train, ev, eval_ratio=0.2, seed=1)
            self.assertEqual((train_n, eval_n), (8, 2))
            self.assertTrue(check_data(train).ok)
            self.assertTrue(check_data(ev).ok)


class ProjectTests(unittest.TestCase):
    def test_demo_command(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "demo"
            result = subprocess.run([sys.executable, "-m", "unslothkit", "demo", str(path)], cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((path / "START_HERE.md").exists())
            self.assertTrue(check_data(path / "data" / "train.jsonl").ok)
            self.assertTrue(check_data(path / "data" / "eval.jsonl").ok)

    def test_create_project(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bot"
            create_project(path, task="support-bot", model_label="tiny-smoke-test")
            self.assertTrue((path / "config.json").exists())
            self.assertTrue((path / "START_HERE.md").exists())
            self.assertTrue((path / "train.py").exists())
            self.assertTrue(check_data(path / "data" / "train.jsonl").ok)
            compile((path / "train.py").read_text(), str(path / "train.py"), "exec")
            compile((path / "chat.py").read_text(), str(path / "chat.py"), "exec")
            compile((path / "eval.py").read_text(), str(path / "eval.py"), "exec")

    def test_recommend(self):
        recs = recommend_models("support-bot", vram_gb=8)
        self.assertTrue(recs)
        self.assertLessEqual(recs[0].min_vram_gb, 8)


if __name__ == "__main__":
    unittest.main()
