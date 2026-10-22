from __future__ import annotations

import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from becuz.schemas import Cause, Investigation

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "docs" / "investigation.schema.json"
CURRENT, BASELINE = 213357.0, 379412.0


def evidence(**overrides) -> dict:
    data = {"evidence_id": "ev1", "table": "becuz.supplier_invoices", "sql": "SELECT 1",
            "row_ids": ["INV-0281"], "value_ngn": -46992.0, "summary": "unit cost up 40%", "via": "local"}
    return {**data, **overrides}


def cause(**overrides) -> dict:
    data = {
        "cause_id": "supplier_cost_rise", "title": "Supplier raised the price of Peak Milk 400g",
        "component": "cogs", "impact_ngn": -46992.0, "impact_evidence_id": "ev1", "share_of_change_pct": 28.3,
        "rank": 1, "origin": "external", "nature": "actionable", "confidence": 0.9, "evidence": [evidence()],
        "falsified_by": [{"test": "unit cost flat across the baseline weeks", "evidence_id": "ev1", "survived": True}],
        "counterfactual_ngn": CURRENT + 46992.0, "depends_on_sources": ["books_files", "pos_files"],
    }
    return {**data, **overrides}


def investigation(**overrides) -> dict:
    change = CURRENT - BASELINE
    data = {
        "run_id": "r1", "status": "complete", "mode": "sample", "synthetic": True, "scenario": "s01",
        "frame": {"question": "Why is my profit down?", "period_start": "2026-10-12", "period_end": "2026-10-18",
                  "baseline_start": "2026-09-14", "baseline_end": "2026-10-11"},
        "headline": {"current_ngn": CURRENT, "baseline_ngn": BASELINE, "change_ngn": change,
                     "change_pct": -43.8, "direction": "down"},
        "tree": [], "causes": [cause()], "ruled_out": [], "not_tested": [],
        "convergence": {"explained_ngn": -46992.0, "explained_pct": 28.3, "unexplained_ngn": change + 46992.0},
        "summary": {"what_happened": "", "why": [], "what_to_do": []}, "owner_questions": [], "limitations": [],
        "stats": {"duration_s": 1, "zetaris_queries": 0, "model_calls": 0, "retries": 0, "models": {}, "via": {}},
        "trace_file": "logs/trace-r1.jsonl",
    }
    return {**data, **overrides}


class SchemaTests(unittest.TestCase):
    def test_committed_json_schema_matches_the_models(self) -> None:
        # The UI builds against docs/investigation.schema.json; it must never drift from the code.
        self.assertEqual(json.loads(SCHEMA_FILE.read_text(encoding="utf-8")), Investigation.model_json_schema())

    def test_a_consistent_investigation_validates(self) -> None:
        parsed = Investigation.model_validate(investigation())
        self.assertEqual(parsed.causes[0].depends_on_sources, ["books_files", "pos_files"])

    def test_impact_must_match_its_evidence(self) -> None:
        with self.assertRaises(ValidationError):
            Cause.model_validate(cause(impact_ngn=-99999.0, counterfactual_ngn=CURRENT + 99999.0))
        with self.assertRaises(ValidationError):
            Cause.model_validate(cause(impact_evidence_id="missing"))

    def test_supported_cause_needs_records(self) -> None:
        with self.assertRaises(ValidationError):
            Cause.model_validate(cause(evidence=[evidence(row_ids=[])]))
        with self.assertRaises(ValidationError):
            Cause.model_validate(cause(evidence=[]))

    def test_figures_that_do_not_add_up_are_rejected(self) -> None:
        bad_counterfactual = investigation(causes=[cause(counterfactual_ngn=1.0)])
        bad_unexplained = investigation(convergence={"explained_ngn": -46992.0, "explained_pct": 28.3, "unexplained_ngn": 0})
        for bad in (bad_counterfactual, bad_unexplained):
            with self.assertRaises(ValidationError):
                Investigation.model_validate(bad)

    def test_unknown_fields_and_bad_values_are_rejected(self) -> None:
        for bad in (cause(typo_field=1), cause(confidence=1.5), cause(status="rejected"),
                    cause(depends_on_sources=["somewhere_else"])):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    Cause.model_validate(bad)


if __name__ == "__main__":
    unittest.main()
