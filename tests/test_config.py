from __future__ import annotations

import contextlib
import os
import tempfile
import unittest
from unittest.mock import patch

from base.config import ROOT, load


class ConfigPathTests(unittest.TestCase):
    def test_relative_evidence_paths_resolve_under_root(self) -> None:
        values = {
            "LEDGER_PATH": "evidence/test-ledger.jsonl",
            "TRACE_PATH": "evidence/test-trace.jsonl",
            "MEMORY_PATH": "evidence/test-memory.json",
        }
        with patch.dict(os.environ, values, clear=False):
            with tempfile.TemporaryDirectory() as tmp:
                with contextlib.chdir(tmp):
                    config = load()

        self.assertEqual(config.ledger_path, ROOT / "evidence/test-ledger.jsonl")
        self.assertEqual(config.trace_path, ROOT / "evidence/test-trace.jsonl")
        self.assertEqual(config.memory_path, ROOT / "evidence/test-memory.json")
        self.assertTrue(config.ledger_path.is_absolute())


if __name__ == "__main__":
    unittest.main()
