from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from base.pipeline import Pipeline


def sample_pipeline(tmp: str) -> Pipeline:
    config = SimpleNamespace(
        sample_mode=True,
        ledger_path=Path(tmp) / "ledger.jsonl",
        nightshift_base_url="http://127.0.0.1:9/v1",
        nightshift_token="",
        nightshift_model="",
        nvidia_base_url="http://127.0.0.1:9/v1",
        nvidia_api_key="",
        nvidia_model="",
    )
    return Pipeline(config)


class PipelineQueryTests(unittest.TestCase):
    def test_trailing_semicolons_are_not_sent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = sample_pipeline(tmp).query("SELECT 1;;;")
            self.assertTrue(result["ok"])
            self.assertEqual(result["sql"], "SELECT 1")


if __name__ == "__main__":
    unittest.main()
