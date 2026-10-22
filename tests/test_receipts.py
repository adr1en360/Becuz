from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from verify_receipts import verify


class ReceiptVerifyTests(unittest.TestCase):
    def test_appends_proof_event_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.jsonl"
            receipt_path = Path(tmp) / "meterless.json"
            ledger_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "kind": "model",
                                "via": "nightshift",
                                "request_id": "r1",
                                "signed": False,
                                "request": "hello",
                            }
                        ),
                        json.dumps(
                            {
                                "kind": "model",
                                "via": "nightshift",
                                "request_id": "r2",
                                "signed": False,
                                "request": "world",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_path.write_text(
                json.dumps(
                    {
                        "receipts": [
                            {"request_id": "r1", "_proof": {"sig": "x"}, "receipt_id": "rc1"}
                        ]
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(verify(ledger_path, receipt_path), 1)
            records = [
                json.loads(line)
                for line in ledger_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(records[-1]["kind"], "model_receipt")
            self.assertTrue(records[-1]["signed"])
            self.assertEqual(records[-1]["receipt_id"], "rc1")

            self.assertEqual(verify(ledger_path, receipt_path), 0)
            records = [
                json.loads(line)
                for line in ledger_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(sum(record["kind"] == "model_receipt" for record in records), 1)

    def test_failed_write_is_not_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.jsonl"
            receipt_path = Path(tmp) / "meterless.json"
            ledger_path.write_text(
                json.dumps(
                    {
                        "kind": "model",
                        "via": "nightshift",
                        "request_id": "r1",
                        "signed": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_path.write_text(
                json.dumps({"receipts": [{"request_id": "r1", "_proof": {"sig": "x"}}]}),
                encoding="utf-8",
            )
            with patch("verify_receipts.ledger.write", return_value=False):
                self.assertEqual(verify(ledger_path, receipt_path), 0)

    def test_signed_model_gets_proof_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.jsonl"
            receipt_path = Path(tmp) / "meterless.json"
            ledger_path.write_text(
                json.dumps(
                    {
                        "kind": "model",
                        "via": "nightshift",
                        "request_id": "r1",
                        "signed": True,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_path.write_text(
                json.dumps({"receipts": [{"request_id": "r1", "_proof": {"sig": "x"}}]}),
                encoding="utf-8",
            )
            self.assertEqual(verify(ledger_path, receipt_path), 1)
            self.assertEqual(verify(ledger_path, receipt_path), 0)

    def test_duplicate_model_rows_produce_one_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.jsonl"
            receipt_path = Path(tmp) / "meterless.json"
            row = json.dumps(
                {
                    "kind": "model",
                    "via": "nightshift",
                    "request_id": "r1",
                    "signed": False,
                }
            )
            ledger_path.write_text(row + "\n" + row + "\n", encoding="utf-8")
            receipt_path.write_text(
                json.dumps({"receipts": [{"request_id": "r1", "_proof": {"sig": "x"}}]}),
                encoding="utf-8",
            )
            self.assertEqual(verify(ledger_path, receipt_path), 1)


if __name__ == "__main__":
    unittest.main()
