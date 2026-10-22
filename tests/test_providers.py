from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from base.nightshift import NightshiftClient, find_receipt
from base.pipeline import Pipeline
from base.providers import ProviderError


class FakeClient:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    def complete(self, messages, model=None):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.body).encode("utf-8")


class RawResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def make_pipeline(tmp: str, nightshift=None) -> Pipeline:
    config = SimpleNamespace(
        sample_mode=False,
        has_nightshift=nightshift is not None,
        ledger_path=Path(tmp) / "ledger.jsonl",
        nightshift_base_url="http://nightshift",
        nightshift_token="token",
        nightshift_model="meterless/auto",
    )
    pipeline = Pipeline(config)
    if nightshift is not None:
        pipeline.nightshift = nightshift
    return pipeline


class ProviderTests(unittest.TestCase):
    def test_nightshift_failure_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = make_pipeline(tmp, FakeClient(error=ProviderError("nightshift", 500, "down")))
            with self.assertRaises(ProviderError) as caught:
                pipeline.ask("hello")
        self.assertIn("nightshift", str(caught.exception))

    def test_no_provider_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = make_pipeline(tmp)
            with self.assertRaises(ProviderError):
                pipeline.ask("hello")

    def test_find_receipt_requires_matching_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "meterless.json"
            path.write_text(
                json.dumps(
                    {
                        "receipts": [
                            {"request_id": "r1"},
                            {"request_id": "r1", "_proof": {"sig": "x"}},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(find_receipt("r1", path, tries=1)["_proof"], {"sig": "x"})
            self.assertEqual(find_receipt("missing", path, tries=1), {})

            path.write_bytes(b"\xff")
            self.assertEqual(find_receipt("r1", path, tries=1), {})

            path.write_text("[]", encoding="utf-8")
            self.assertEqual(find_receipt("r1", path, tries=1), {})

    def test_find_receipt_retries_until_proof_appears(self) -> None:
        empty = json.dumps({"receipts": []})
        settled = json.dumps(
            {"receipts": [{"request_id": "r1", "_proof": {"sig": "late"}}]}
        )
        with patch.object(Path, "read_text", side_effect=[empty, settled]):
            receipt = find_receipt("r1", Path("unused.json"), tries=2, delay=0)
        self.assertEqual(receipt["_proof"], {"sig": "late"})

    def test_nightshift_empty_choices(self) -> None:
        with patch("urllib.request.urlopen", return_value=FakeResponse({"choices": []})):
            client = NightshiftClient("http://nightshift", "token", "model")
            with self.assertRaises(ProviderError):
                client.complete([{"role": "user", "content": "hi"}])

    def test_nightshift_empty_answer(self) -> None:
        body = {"id": "r1", "choices": [{"message": {"content": ""}}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
            client = NightshiftClient("http://nightshift", "token", "model")
            with self.assertRaises(ProviderError):
                client.complete([{"role": "user", "content": "hi"}])

    def test_nightshift_invalid_content_part(self) -> None:
        body = {"id": "r1", "choices": [{"message": {"content": [{"text": 123}]}}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
            client = NightshiftClient("http://nightshift", "token", "model")
            with self.assertRaises(ProviderError):
                client.complete([{"role": "user", "content": "hi"}])

    def test_nightshift_think_block_only_is_empty(self) -> None:
        body = {"id": "r1", "choices": [{"message": {"content": "<think>hmm</think>  "}}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
            client = NightshiftClient("http://nightshift", "token", "model")
            with self.assertRaises(ProviderError):
                client.complete([{"role": "user", "content": "hi"}])

    def test_nightshift_reasoning_only_is_empty(self) -> None:
        body = {"id": "", "choices": [{"message": {"reasoning_content": "ready"}}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
            with self.assertRaises(ProviderError):
                NightshiftClient("http://nightshift", "token", "model").complete(
                    [{"role": "user", "content": "hi"}]
                )

    def test_nightshift_invalid_utf8(self) -> None:
        with patch("urllib.request.urlopen", return_value=RawResponse(b"\xff")):
            with self.assertRaises(ProviderError):
                NightshiftClient("http://nightshift", "token", "model").complete(
                    [{"role": "user", "content": "hi"}]
                )

    def test_nightshift_signs_only_with_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "ai.meterless.runtime" / "meterless.json"
            receipt_path.parent.mkdir(parents=True)
            receipt_path.write_text(
                json.dumps(
                    {"receipts": [{"request_id": "r1", "_proof": {"sig": "x"}}]}
                ),
                encoding="utf-8",
            )
            body = {"id": "r1", "choices": [{"message": {"content": "ok"}}]}
            with patch.dict(os.environ, {"APPDATA": tmp}, clear=False):
                with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
                    completion = NightshiftClient(
                        "http://nightshift", "token", "model"
                    ).complete([{"role": "user", "content": "hi"}])
        self.assertTrue(completion.signed)
        self.assertEqual(completion.receipt["_proof"], {"sig": "x"})


if __name__ == "__main__":
    unittest.main()
