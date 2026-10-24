from __future__ import annotations

import contextlib
import os
import tempfile
import unittest
from unittest.mock import patch

from becuz import ledger
from becuz.config import ROOT, load


class ConfigPathTests(unittest.TestCase):
    def test_relative_evidence_paths_resolve_under_root(self) -> None:
        values = {
            "LEDGER_PATH": "evidence/test-ledger.jsonl",
            "TRACE_PATH": "evidence/test-trace.jsonl",
        }
        with patch.dict(os.environ, values, clear=False):
            with tempfile.TemporaryDirectory() as tmp:
                with contextlib.chdir(tmp):
                    config = load()

        self.assertEqual(config.ledger_path, ROOT / "evidence/test-ledger.jsonl")
        self.assertEqual(config.trace_path, ROOT / "evidence/test-trace.jsonl")
        self.assertTrue(config.ledger_path.is_absolute())

    def test_none_disables_a_path(self) -> None:
        values = {"LEDGER_PATH": "none", "TRACE_PATH": "None"}
        with patch.dict(os.environ, values, clear=False):
            config = load()
        self.assertIsNone(config.ledger_path)
        self.assertIsNone(config.trace_path)

    def test_blank_numbers_use_defaults(self) -> None:
        # A judge who copies .env.example and clears every value must still start.
        with patch.dict(os.environ, {"SERVER_PORT": ""}, clear=False):
            config = load()
        self.assertEqual(config.server_port, 8000)

    def test_bad_numbers_use_defaults(self) -> None:
        with patch.dict(os.environ, {"SERVER_PORT": "80x"}, clear=False):
            with contextlib.redirect_stderr(None):
                config = load()
        self.assertEqual(config.server_port, 8000)

    def test_off_words_disable_a_path(self) -> None:
        for word in ("null", "off", "false", "OFF"):
            with self.subTest(word=word):
                with patch.dict(os.environ, {"LEDGER_PATH": word}, clear=False):
                    self.assertIsNone(load().ledger_path)


class LedgerTests(unittest.TestCase):
    def test_disabled_path_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.chdir(tmp):
                self.assertFalse(ledger.write(None, {"kind": "x"}))
                self.assertEqual(os.listdir(tmp), [])


if __name__ == "__main__":
    unittest.main()
