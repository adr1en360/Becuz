from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from becuz.investigate import BadRequest, investigate
from data.generator import ROOT, SCENARIOS

TRACE_FIELDS = {"timestamp", "run_id", "agent_name", "action", "input_summary", "output_summary",
                "target_agent", "confidence", "retry_count", "status"}
# s01 keeps natural day-to-day variation, so its real dip in units sold is a true, unplanted cause.
UNPLANTED_BUT_REAL = {"s01": {"sales_volume_drop"}}


class InvestigateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.config = SimpleNamespace(sample_mode=True, ledger_path=None, trace_path=Path(cls.tmp.name) / "trace.jsonl")
        cls.reports = {s: investigate({"question": "Why is my profit down this week?", "scenario": s}, cls.config)
                       for s in SCENARIOS}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def key(self, scenario: str) -> dict:
        return json.loads((ROOT / scenario / "answer_key.json").read_text(encoding="utf-8"))

    @staticmethod
    def findings(report: dict) -> list[dict]:
        return report["causes"] + report["cash_gaps"]

    def test_finds_exactly_the_planted_causes(self) -> None:
        for scenario, report in self.reports.items():
            with self.subTest(scenario=scenario):
                planted = {c["cause_id"] for c in self.key(scenario)["causes"]}
                found = {c["cause_id"] for c in self.findings(report)}
                self.assertEqual(found, planted | UNPLANTED_BUT_REAL.get(scenario, set()))

    def test_missing_transfers_are_cash_not_profit(self) -> None:
        for scenario, report in self.reports.items():
            with self.subTest(scenario=scenario):
                self.assertNotIn("transfer_leakage", {c["cause_id"] for c in report["causes"]})
                self.assertEqual(len(report["summary"]["cash"]), len(report["cash_gaps"]))
        # s04's only planted problem is missing transfers, so its profit did not fall.
        self.assertEqual([c["cause_id"] for c in self.reports["s04"]["cash_gaps"]], ["transfer_leakage"])
        self.assertNotEqual(self.reports["s04"]["headline"]["direction"], "down")

    def test_red_herrings_are_ruled_out(self) -> None:
        for scenario, report in self.reports.items():
            ruled_out = {r["cause_id"] for r in report["ruled_out"]}
            for herring in self.key(scenario)["red_herrings"]:
                with self.subTest(scenario=scenario, herring=herring):
                    self.assertIn(herring, ruled_out)

    def test_impacts_match_the_answer_key(self) -> None:
        for scenario, report in self.reports.items():
            found = {c["cause_id"]: c["impact_ngn"] for c in self.findings(report)}
            for cause in self.key(scenario)["causes"]:
                with self.subTest(scenario=scenario, cause=cause["cause_id"]):
                    self.assertAlmostEqual(found[cause["cause_id"]], cause["impact_ngn"], delta=1)

    def test_each_run_writes_its_own_trace_with_the_required_fields(self) -> None:
        for report in self.reports.values():
            lines = [json.loads(line) for line in (Path(self.tmp.name) / report["trace_file"]).read_text(encoding="utf-8").splitlines()]
            self.assertTrue(lines)
            self.assertTrue(all(TRACE_FIELDS <= set(line) and line["run_id"] == report["run_id"] for line in lines))
            self.assertEqual({line["agent_name"] for line in lines}, {"Planner", "Investigator", "Checker", "Writer"})

    def test_bad_requests_are_refused(self) -> None:
        for bad in ({}, {"question": ""}, {"question": "x" * 501}, {"question": "why?", "week_start": "monday"},
                    {"question": "why?", "scenario": "s99"}, ["not", "an", "object"]):
            with self.subTest(bad=bad):
                with self.assertRaises(BadRequest):
                    investigate(bad, self.config)

    def test_a_week_that_is_not_monday_to_sunday_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            investigate({"question": "why?", "week_start": "2027-01-04"}, self.config)


if __name__ == "__main__":
    unittest.main()
