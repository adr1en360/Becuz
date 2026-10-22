from __future__ import annotations

import unittest

from scripts.admin import hide
from becuz.usl import SOURCES
from scripts.zetaris_setup import statements


class ZetarisSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = statements("s01", "my-bucket", "AKIAEXAMPLEKEY000000", "secret/value+x")

    def test_one_database_per_source_then_its_tables(self) -> None:
        tables = sum(len(t) for t in SOURCES.values())
        self.assertEqual(len(self.plan), len(SOURCES) + tables)
        self.assertTrue(self.plan[0].startswith("CREATE LIGHTNING DATABASE pos_files"))
        self.assertIn('path "s3a://my-bucket/becuz/s01/bank_statement.csv"', "".join(self.plan))

    def test_never_writes_back_to_the_bucket(self) -> None:
        # sourceTable makes Zetaris write data to the path.
        self.assertFalse(any("sourceTable" in sql for sql in self.plan))

    def test_hide_removes_every_secret(self) -> None:
        shown = "\n".join(hide(sql, "AKIAEXAMPLEKEY000000", "secret/value+x") for sql in self.plan)
        self.assertNotIn("secret/value+x", shown)
        self.assertNotIn("AKIAEXAMPLEKEY000000", shown)
        self.assertIn('awsAccessKeyId "***"', shown)


if __name__ == "__main__":
    unittest.main()
