from __future__ import annotations

import unittest

from base import sample


class SampleTests(unittest.TestCase):
    def test_databases(self) -> None:
        self.assertEqual(sample.rows("SHOW LIGHTNING DATABASES")[0][0], "SAMPLE_DB")

    def test_select_one(self) -> None:
        self.assertEqual(sample.rows("SELECT 1 AS one"), [[1]])

    def test_ready(self) -> None:
        completion = sample.completion(
            [{"role": "user", "content": "Reply with the single word: ready"}]
        )
        self.assertEqual(completion.text, "ready")
        self.assertEqual(completion.via, "sample")


if __name__ == "__main__":
    unittest.main()
