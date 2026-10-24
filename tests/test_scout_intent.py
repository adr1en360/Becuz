"""Scout Intent checks, one per MUST rule of the spec's execution contract.

The spec ships no Python conformance suite (only Node evals), so these tests are
written from its hard rules: engines/scout-intent/AGENTS.md and docs/execution-contract.md.
"""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from becuz.engines.scout_intent import QUERIES_MAX, ContractGate, ContractRefused, Scout


class FakeWarehouse:
    via, usl = "local", "becuz"

    def __init__(self):
        self.sent = []

    def query(self, sql: str) -> list[dict]:
        self.sent.append(sql)
        return [{"ok": 1}]


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 23, 9, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


class ScoutIntentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "scout.jsonl"
        self.clock = Clock()
        self.scout = Scout(key=b"test-key", log_path=self.log, clock=self.clock)
        self.contract = self.scout.decide("Why is my profit down this week?", "run-1")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def events(self) -> list[str]:
        return [json.loads(line)["kind"] for line in self.log.read_text(encoding="utf-8").splitlines()]

    def test_sign_verify_roundtrip(self) -> None:
        self.scout.verify(self.contract)
        self.assertEqual(self.contract["signedBy"], "scout")
        self.assertEqual(self.contract["intent"]["primary"], "profit.explain_change")

    def test_tampered_contract_is_refused(self) -> None:
        widened = copy.deepcopy(self.contract)
        widened["scope"]["capabilities"].append("staff_salaries")
        with self.assertRaises(ContractRefused) as caught:
            self.scout.verify(widened)
        self.assertEqual(caught.exception.reason, "tampered")

    def test_unsigned_contract_is_refused(self) -> None:
        unsigned = {k: v for k, v in self.contract.items() if k != "signature"}
        with self.assertRaises(ContractRefused):
            self.scout.verify(unsigned)

    def test_expired_contract_is_refused_and_logged(self) -> None:
        self.clock.now += timedelta(minutes=6)
        with self.assertRaises(ContractRefused) as caught:
            self.scout.verify(self.contract)
        self.assertEqual(caught.exception.reason, "expired")
        self.assertIn("contract.expired", self.events())

    def test_gate_reissues_an_expired_contract_instead_of_extending_it(self) -> None:
        gate = ContractGate(FakeWarehouse(), self.scout)
        first = gate.open("Why is my profit down?", "run-2")
        self.clock.now += timedelta(minutes=6)
        gate.query("SELECT 1 FROM becuz.sales")
        self.assertNotEqual(gate.contract["contractId"], first["contractId"])
        self.assertEqual(gate.contract["parentId"], first["contractId"])
        self.assertEqual(gate.contract["traceId"], first["traceId"])
        lifetime = datetime.fromisoformat(first["expiresAt"]) - datetime.fromisoformat(first["issuedAt"])
        self.assertEqual(lifetime, timedelta(minutes=5))

    def test_query_on_a_table_outside_the_contract_is_refused(self) -> None:
        wh = FakeWarehouse()
        gate = ContractGate(wh, self.scout)
        gate.open("Why is my profit down?", "run-3")
        with self.assertRaises(ContractRefused) as caught:
            gate.query("SELECT * FROM becuz.staff_salaries")
        self.assertIn("scope-mismatch", caught.exception.reason)
        self.assertEqual(wh.sent, [])  # the refused query never reached the warehouse
        self.assertIn("contract.refused", self.events())

    def test_budget_is_enforced(self) -> None:
        gate = ContractGate(FakeWarehouse(), self.scout)
        gate.open("Why is my profit down?", "run-4")
        for _ in range(QUERIES_MAX):
            gate.query("SELECT 1 FROM becuz.sales")
        with self.assertRaises(ContractRefused) as caught:
            gate.query("SELECT 1 FROM becuz.sales")
        self.assertEqual(caught.exception.reason, "budget-exhausted")

    def test_no_query_runs_without_a_contract(self) -> None:
        with self.assertRaises(ContractRefused):
            ContractGate(FakeWarehouse(), self.scout).query("SELECT 1 FROM becuz.sales")

    def test_off_topic_question_scores_zero(self) -> None:
        self.assertEqual(self.scout.classify("What is the weather in Lagos tomorrow?")[1], 0)

    def test_events_are_written_as_jsonl(self) -> None:
        self.assertEqual(self.events()[0], "contract.issued")

    def test_investigation_refuses_off_topic_questions(self) -> None:
        from becuz.investigate import BadRequest, investigate

        config = SimpleNamespace(sample_mode=True, ledger_path=None, trace_path=None)
        with self.assertRaises(BadRequest):
            investigate({"question": "What is the weather tomorrow?", "scenario": "s02"}, config)


if __name__ == "__main__":
    unittest.main()
