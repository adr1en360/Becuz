from __future__ import annotations

import unittest
from datetime import date, timedelta

from becuz.metrics import baseline_days


class BaselineTests(unittest.TestCase):
    def test_a_week_is_compared_with_the_4_weeks_before_it(self) -> None:
        start = date(2026, 10, 12)
        self.assertEqual(baseline_days(start, start + timedelta(days=6)),
                         [start - timedelta(days=28 - d) for d in range(28)])

    def test_a_short_period_is_compared_with_the_same_weekdays(self) -> None:
        start = date(2026, 10, 16)  # Friday to Sunday
        days = baseline_days(start, start + timedelta(days=2))
        self.assertEqual(len(days), 12)
        self.assertEqual({d.weekday() for d in days}, {4, 5, 6})
        self.assertEqual((days[0], days[-1]), (date(2026, 9, 18), date(2026, 10, 11)))

    def test_a_longer_period_moves_back_by_whole_weeks_without_overlap(self) -> None:
        start = date(2026, 10, 9)
        days = baseline_days(start, start + timedelta(days=9))  # 10 days, so windows step back 14 days
        self.assertEqual(len(set(days)), 40)
        self.assertEqual(days[-1], start - timedelta(days=5))
        self.assertTrue(all(d < start for d in days))

    def test_only_1_to_28_real_days_pass(self) -> None:
        start = date(2026, 10, 12)
        for end in (start - timedelta(days=1), start + timedelta(days=28)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                baseline_days(start, end)
        with self.assertRaises(ValueError):
            baseline_days("2026-10-12'; DROP", start)


if __name__ == "__main__":
    unittest.main()
