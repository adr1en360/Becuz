from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from becuz.engines.scout_intent import Scout
from becuz.investigate import investigate


class RoutingTests(unittest.TestCase):
    def test_each_everyday_question_goes_to_its_answer(self) -> None:
        scout = Scout(key=b"t")
        for question, intent in (("What sold the highest?", "answer.top_sellers"), ("Which product sold least?", "answer.top_sellers"),
                                 ("How much did I sell?", "answer.totals"), ("How much money is missing?", "answer.missing_money"),
                                 ("What are my biggest expenses?", "answer.expenses"), ("What did I spend money on?", "answer.expenses"),
                                 ("Is any money missing?", "answer.missing_money"), ("Why is my profit down?", "profit.explain_change"),
                                 ("Why are my sales down?", "profit.explain_change"), ("Where did my money go?", "profit.explain_change"),
                                 ("How is my shop doing?", "profit.explain_change")):
            with self.subTest(question=question):
                self.assertEqual(scout.classify(question)[0], intent)


class AnswerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.config = SimpleNamespace(sample_mode=True, ledger_path=None, trace_path=Path(cls.tmp.name) / "trace.jsonl")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def ask(self, question: str, days: int = 7) -> dict:
        return investigate({"question": question, "scenario": "s01", "days": days}, self.config)

    def test_a_direct_question_is_answered_from_records_without_an_investigation(self) -> None:
        report = self.ask("What sold the highest?")
        answer = report["answer"]
        self.assertEqual(answer["kind"], "top_sellers")
        self.assertEqual(answer["sentence"], "Mama Gold Rice 5kg sold most in these 7 days: ₦352,800 from 36 units, the same as usual.")
        values = [r["value_ngn"] for r in answer["rows"]]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual((report["causes"], report["ruled_out"], report["stats"]["model_calls"]), ([], [], 0))

    def test_least_sold_ranks_from_the_bottom(self) -> None:
        values = [r["value_ngn"] for r in self.ask("Which product sold least?", days=3)["answer"]["rows"]]
        self.assertEqual(values, sorted(values))

    def test_totals_match_the_profit_tree(self) -> None:
        report = self.ask("How much did I sell?")
        rows = {r["label"]: r["value_ngn"] for r in report["answer"]["rows"]}
        self.assertEqual(rows["Profit"], report["headline"]["current_ngn"])
        self.assertAlmostEqual(rows["Sales"] - rows["Cost of stock sold"] - rows["Wasted stock"] - rows["Running costs"], rows["Profit"], delta=0.05)

    def test_missing_money_matches_the_planted_transfers(self) -> None:
        answer = self.ask("Is any money missing?")["answer"]
        self.assertEqual(answer["sentence"], "₦18,200 from 6 transfer sales in these 7 days never reached the bank.")
        self.assertEqual(len(answer["row_ids"]), 6)

    def test_expenses_rank_by_category(self) -> None:
        answer = self.ask("What are my biggest expenses?")["answer"]
        self.assertEqual(answer["rows"][0]["label"], "diesel")
        self.assertTrue(answer["sql"].startswith("SELECT category AS label"))

    def test_a_why_question_still_investigates(self) -> None:
        report = self.ask("Why is my profit down?")
        self.assertIsNone(report["answer"])
        self.assertEqual(len(report["causes"]), 3)


if __name__ == "__main__":
    unittest.main()
