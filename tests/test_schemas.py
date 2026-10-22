from __future__ import annotations

import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from becuz.schemas import Cause, Investigation

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "docs" / "investigation.schema.json"


def cause(**overrides) -> dict:
    data = {
        "cause_id": "supplier_cost_rise", "title": "Supplier raised the price of Peak Milk 400g",
        "status": "supported", "impact_ngn": -46992.0, "share_of_drop_pct": 28.3, "rank": 1,
        "origin": "external", "nature": "actionable", "confidence": 0.9, "evidence": [],
        "falsified_by": ["unit cost flat across the baseline weeks: not the case"],
        "counterfactual_ngn": 260349.0, "depends_on_sources": ["books_files", "pos_files"],
    }
    return {**data, **overrides}


class SchemaTests(unittest.TestCase):
    def test_committed_json_schema_matches_the_models(self) -> None:
        # The UI builds against docs/investigation.schema.json; it must never drift from the code.
        self.assertEqual(json.loads(SCHEMA_FILE.read_text(encoding="utf-8")), Investigation.model_json_schema())

    def test_cause_carries_the_three_ui_fields(self) -> None:
        parsed = Cause.model_validate(cause())
        self.assertEqual(parsed.depends_on_sources, ["books_files", "pos_files"])
        self.assertEqual(parsed.counterfactual_ngn, 260349.0)
        self.assertTrue(parsed.falsified_by)

    def test_unknown_fields_and_bad_values_are_rejected(self) -> None:
        for bad in (cause(typo_field=1), cause(confidence=1.5), cause(status="maybe")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    Cause.model_validate(bad)


if __name__ == "__main__":
    unittest.main()
