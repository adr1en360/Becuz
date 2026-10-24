from __future__ import annotations

import json
import unittest
from datetime import date

from becuz.safety import is_read_only
from becuz.adapters.local_sql import LocalWarehouse
from becuz.catalogue import CATALOGUE, measure, render
from data.generator import ROOT, SCENARIOS

WEEK = (date(2026, 10, 12), date(2026, 10, 18))


class CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.measured = {}
        for scenario in SCENARIOS:
            wh = LocalWarehouse(scenario)
            cls.measured[scenario] = {cause: measure(wh, cause, *WEEK) for cause in CATALOGUE}

    def key(self, scenario: str) -> dict:
        return json.loads((ROOT / scenario / "answer_key.json").read_text(encoding="utf-8"))

    def test_planted_causes_measure_the_answer_key(self) -> None:
        for scenario in SCENARIOS:
            for cause in self.key(scenario)["causes"]:
                with self.subTest(scenario=scenario, cause=cause["cause_id"]):
                    m = self.measured[scenario][cause["cause_id"]]
                    self.assertAlmostEqual(m.effect_ngn, cause["impact_ngn"], delta=1)
                    self.assertTrue(m.row_ids, "a planted cause must return its records")

    def test_unplanted_causes_measure_zero_in_steady_scenarios(self) -> None:
        for scenario, spec in SCENARIOS.items():
            if not spec.get("steady"):
                continue
            planted = {c["cause_id"] for c in self.key(scenario)["causes"]}
            for cause in set(CATALOGUE) - planted:
                with self.subTest(scenario=scenario, cause=cause):
                    self.assertAlmostEqual(self.measured[scenario][cause].effect_ngn, 0, delta=1)

    def test_red_herrings_are_never_a_loss(self) -> None:
        for scenario in SCENARIOS:
            for herring in self.key(scenario)["red_herrings"]:
                with self.subTest(scenario=scenario, herring=herring):
                    self.assertGreater(self.measured[scenario][herring].effect_ngn, -1)

    def test_templates_are_read_only(self) -> None:
        for spec in CATALOGUE.values():
            for template in (spec.effect_sql, spec.records_sql):
                with self.subTest(cause=spec.cause_id):
                    self.assertTrue(is_read_only(render(template, "becuz", *WEEK)))

    def test_model_cannot_pick_an_unknown_cause_or_inject_dates(self) -> None:
        wh = LocalWarehouse("s01")
        with self.assertRaises(KeyError):
            measure(wh, "made_up_cause", *WEEK)
        with self.assertRaises(ValueError):
            measure(wh, "transfer_leakage", "2026-10-12' OR 1=1 --", WEEK[1])


if __name__ == "__main__":
    unittest.main()
