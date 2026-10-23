"""H-MEM checks: a Python port of the spec's conformance vectors (engines/hmem/conformance/vectors/vectors.json,
same IDs and expected numbers), plus the Becuz confirm-then-recall feature test."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from becuz.engines.hmem import HMEM
from becuz.investigate import BadRequest, confirm, investigate


class ConformancePortTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = HMEM()

    def test_rv_001_a_record_without_a_source_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.memory.add("no source here", "")

    def test_rv_002_a_record_with_a_source_is_accepted(self) -> None:
        self.assertTrue(self.memory.add("valid record", "test"))

    def test_fd_feedback_deltas_and_clamps(self) -> None:
        # (id, start, kind, expected confidence, expected access delta)
        vectors = [("fd-001", 0.7, "helpful", 0.75, 1), ("fd-002", 0.7, "not_helpful", 0.67, 0),
                   ("fd-003", 0.7, "wrong", 0.5, 0), ("fd-004", 0.1, "wrong", 0.0, 0), ("fd-005", 0.98, "helpful", 1.0, 1)]
        for vector_id, start, kind, expected, access in vectors:
            with self.subTest(vector_id):
                memory_id = self.memory.add("a fact", "test", confidence=start)
                record = self.memory.feedback(memory_id, kind)
                self.assertAlmostEqual(record["confidence"], expected)
                self.assertEqual(record["accessCount"], access)
                if kind == "wrong":
                    self.assertIn("review", record["tags"])

    def test_ro_001_a_superseded_record_ranks_below_a_fresh_one(self) -> None:
        fresh = self.memory.add("we deploy the api with docker on mondays", "test", confidence=0.9)
        old = self.memory.add("we deploy the api with docker on fridays", "test", confidence=0.9)
        self.memory.supersede(old, fresh)
        order = [h["memory"]["id"] for h in self.memory.query("when do we deploy the api with docker")["results"]]
        self.assertEqual(order, [fresh, old])

    def test_ro_002_confidence_multiplies_the_score(self) -> None:
        high = self.memory.add("the deploy window is monday morning", "test", layer="working", confidence=0.9)
        low = self.memory.add("the deploy window is monday morning", "test", layer="working", confidence=0.4)
        order = [h["memory"]["id"] for h in self.memory.query("deploy window")["results"]]
        self.assertEqual(order, [high, low])

    def test_la_001_the_ledger_reconstructs_create_then_feedback(self) -> None:
        memory_id = self.memory.add("a fact", "test", confidence=0.7)
        self.memory.feedback(memory_id, "wrong")
        actions = [(e["action"], e["previousState"], e["newState"]) for e in self.memory.ledger]
        self.assertEqual(actions[0], ("create", None, {"confidence": 0.7}))
        self.assertEqual(actions[1][0], "feedback.wrong")
        self.assertEqual((actions[1][1]["confidence"], actions[1][2]["confidence"]), (0.7, 0.5))

    def test_query_returns_a_structured_payload(self) -> None:
        self.memory.add("supplier raised the price of milk", "test", tags=["owner_confirmed"])
        payload = self.memory.query("why did milk cost more", tags=["owner_confirmed"])
        self.assertEqual(payload["strategy"], "task_focused")
        self.assertIn("retrievalReason", payload["results"][0])


class ConfirmThenRecallTests(unittest.TestCase):
    def test_a_confirmed_cause_is_tested_first_next_time_and_gains_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            config = SimpleNamespace(sample_mode=True, ledger_path=None, trace_path=logs / "trace.jsonl")
            first = investigate({"question": "Why is my profit down?", "scenario": "s04"}, config)
            memory_id = confirm(first["run_id"], "transfer_leakage", config)
            second = investigate({"question": "Why is my profit down?", "scenario": "s01"}, config)
            trace = [json.loads(l) for l in (logs / f"trace-{second['run_id']}.jsonl").read_text(encoding="utf-8").splitlines()]
            first_test = next(l for l in trace if l["action"] == "test_cause")
            stored = json.loads((logs / "hmem.json").read_text(encoding="utf-8"))
        self.assertEqual(first_test["input_summary"], "transfer_leakage")
        record = next(r for r in stored if r["id"] == memory_id)
        self.assertEqual((record["confidence"], record["source"], record["agentId"]), (0.75, "owner_confirm", "owner"))

    def test_only_a_supported_cause_can_be_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = SimpleNamespace(sample_mode=True, ledger_path=None, trace_path=Path(tmp) / "trace.jsonl")
            run = investigate({"question": "Why is my profit down?", "scenario": "s04"}, config)
            with self.assertRaises(BadRequest):
                confirm(run["run_id"], "pos_charge_rise", config)  # the Checker rejected it
            with self.assertRaises(BadRequest):
                confirm("inv-0000000000", "transfer_leakage", config)  # no such run


if __name__ == "__main__":
    unittest.main()
