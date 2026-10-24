"""World Model checks: a Python port of the spec's conformance suite (engines/world-model/conformance),
keeping its check IDs, plus Becuz feature tests for the shared claims list."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from becuz.engines.world_model import WorldModel, decide, entity_id, normalize_name

SOURCE = {"kind": "zetaris", "table": "becuz.products", "pk": "P001"}


class Clock:
    def __init__(self):
        self.tick = 0

    def __call__(self) -> str:
        self.tick += 1
        return f"2026-10-23T09:00:{self.tick:02d}+00:00"


class ConformancePortTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = WorldModel(clock=Clock())

    def test_sid_001_names_normalize_to_one_id(self) -> None:
        self.assertEqual(normalize_name("José  García"), "jose garcia")
        self.assertEqual(entity_id("staff", "José  García"), entity_id("staff", "Jose Garcia"))

    def test_sid_002_distinct_names_and_types_stay_distinct(self) -> None:
        self.assertNotEqual(entity_id("staff", "Tunde"), entity_id("staff", "Amaka"))
        self.assertNotEqual(entity_id("staff", "Tunde"), entity_id("supplier", "Tunde"))

    def test_band_001_merge_decisions(self) -> None:
        self.assertEqual([decide(s) for s in (0.85, 0.84, 0.82, 0.81)], ["auto-merge", "review", "review", "new"])

    def test_prov_001_a_write_without_a_source_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.world.upsert_entity("product", "Peak Milk 400g", {}, "test")

    def test_idem_001_re_ingesting_a_batch_changes_nothing(self) -> None:
        batch = [{"type": "product", "name": "Peak Milk 400g", "source": SOURCE, "properties": {"price": 1650}}]
        self.assertTrue(self.world.ingest(batch, "test"))
        shape = self.world.canonical_shape()
        self.assertFalse(self.world.ingest(batch, "test"))
        self.assertEqual(self.world.canonical_shape(), shape)

    def test_idem_002_a_changed_batch_is_a_change(self) -> None:
        self.world.ingest([{"type": "product", "name": "Peak Milk 400g", "source": SOURCE, "properties": {"price": 1650}}], "t")
        changed = [{"type": "product", "name": "Peak Milk 400g", "source": SOURCE, "properties": {"price": 1800}}]
        self.assertTrue(self.world.ingest(changed, "t"))

    def test_bitemp_001_a_new_status_closes_the_old_one(self) -> None:
        claim = self.world.propose_claim("wastage_spike", "w42", "Investigator", "run-1", effect_ngn=-1)
        proposed_at = self.world.edges[-1]["validFrom"]
        self.world.set_status(claim, "supported", "Checker")
        old = next(e for e in self.world.edges if e["to"] == "proposed")
        self.assertIsNotNone(old["validTo"])
        self.assertEqual(self.world.status(claim), "supported")
        self.assertEqual(self.world.status(claim, at=proposed_at), "proposed")  # point-in-time view

    def test_audit_001_every_mutation_is_audited_in_order(self) -> None:
        claim = self.world.propose_claim("promo_overrun", "w42", "Investigator", "run-1", effect_ngn=-1)
        self.world.set_status(claim, "rejected", "Checker", "no loss")
        seqs = [entry["seq"] for entry in self.world.audit]
        self.assertEqual(seqs, sorted(set(seqs)))
        self.assertEqual([e["action"] for e in self.world.audit], ["upsert", "status", "status"])


class SharedClaimsTests(unittest.TestCase):
    def test_writer_context_holds_only_supported_claims(self) -> None:
        world = WorldModel()
        kept = world.propose_claim("transfer_leakage", "w42", "Investigator", "r", effect_ngn=-28360)
        dropped = world.propose_claim("pos_charge_rise", "w42", "Investigator", "r", effect_ngn=0)
        world.set_status(kept, "supported", "Checker")
        world.set_status(dropped, "rejected", "Checker")
        context = world.context_for("writer")
        self.assertEqual([c["cause_id"] for c in context["claims"]], ["transfer_leakage"])
        self.assertIn("supported", context["selectionReason"])
        self.assertEqual(world.history(dropped), ["proposed", "rejected"])

    def test_a_real_run_records_every_verdict_in_the_world_log(self) -> None:
        from becuz.investigate import investigate

        with tempfile.TemporaryDirectory() as tmp:
            config = SimpleNamespace(sample_mode=True, ledger_path=None, trace_path=Path(tmp) / "trace.jsonl")
            report = investigate({"question": "Why is my profit down?", "scenario": "s04"}, config)
            events = [json.loads(line) for line in (Path(tmp) / "world.jsonl").read_text(encoding="utf-8").splitlines()]
        statuses = [e["status"] for e in events if e["kind"] == "world.status"]
        self.assertEqual(statuses.count("proposed"), 6)  # every catalogue cause was claimed
        self.assertEqual(statuses.count("supported"), len(report["causes"]) + len(report["cash_gaps"]))


if __name__ == "__main__":
    unittest.main()
