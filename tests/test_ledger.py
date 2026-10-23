from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from becuz import ledger


class LedgerTests(unittest.TestCase):
    def test_write_redacts_and_failure_is_non_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            self.assertTrue(ledger.write(path, {"ok": True, "token": "nvapi-abcdef"}))
            record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
            self.assertTrue(record["ok"])
            self.assertEqual(record["token"], "nvapi-REDACTED")
            self.assertIn("ts", record)

            blocker = Path(tmp) / "blocked"
            blocker.write_text("x", encoding="utf-8")
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                self.assertFalse(ledger.write(blocker / "ledger.jsonl", {"ok": False}))
                self.assertFalse(ledger.write(Path(tmp) / "bad.jsonl", {"bad": object()}))
            self.assertIn("ledger:", error.getvalue())
            self.assertFalse((blocker / "ledger.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
