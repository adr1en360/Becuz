from __future__ import annotations

import json
import unittest
from pathlib import Path

from base.scout import classify

CASES = json.loads((Path(__file__).resolve().parent.parent / "scout_cases.json").read_text(encoding="utf-8"))


class ScoutTests(unittest.TestCase):
    def test_cases(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                decision = classify(case["request"])
                self.assertEqual(decision.tool, case["tool"], case["name"])


if __name__ == "__main__":
    unittest.main()
