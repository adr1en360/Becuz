from __future__ import annotations

import json
import unittest
from pathlib import Path

import duckdb
import sqlglot

from base.tools import is_read_only
from data.generator import ROOT
from becuz.usl import DDL, SOURCES, activations
from scripts.zetaris_usl import statements

S01 = ROOT / "s01"
KEY = json.loads((S01 / "answer_key.json").read_text(encoding="utf-8"))


def run_spark(db, sql: str) -> list:
    """Run Zetaris (Spark) SQL locally, the way sample mode will."""
    return db.execute(sqlglot.transpile(sql, read="spark", write="duckdb")[0]).fetchall()


class UslTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = duckdb.connect()
        for source, tables in SOURCES.items():
            cls.db.execute(f"CREATE SCHEMA {source}")
            for table in tables:
                path = (S01 / f"{table}.csv").as_posix()
                cls.db.execute(f"CREATE TABLE {source}.{table} AS SELECT * FROM read_csv_auto('{path}')")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.close()

    def test_every_activation_is_read_only_and_runs(self) -> None:
        for table, sql in activations().items():
            with self.subTest(table=table):
                self.assertTrue(is_read_only(sql))
                self.assertTrue(run_spark(self.db, sql))

    def test_every_ddl_table_is_activated(self) -> None:
        declared = [line.split()[2] for line in DDL.splitlines() if line.startswith("CREATE TABLE")]
        self.assertEqual(sorted(declared), sorted(activations()))

    def test_transfer_check_finds_exactly_the_leaked_sales(self) -> None:
        rows = run_spark(self.db, f"SELECT sale_id FROM ({activations()['transfer_check']}) t "
                                  "WHERE bank_txn_id IS NULL ORDER BY sale_id")
        self.assertEqual([r[0] for r in rows], KEY["leaked_sale_ids"])

    def test_daily_pnl_leakage_matches_answer_key(self) -> None:
        week = KEY["final_week"]
        (leak,) = run_spark(self.db, f"SELECT SUM(leakage_ngn) FROM ({activations()['daily_pnl']}) p "
                                     f"WHERE day BETWEEN DATE '{week['start']}' AND DATE '{week['end']}'")[0]
        impact = next(c["impact_ngn"] for c in KEY["causes"] if c["cause_id"] == "transfer_leakage")
        self.assertAlmostEqual(-leak, impact, delta=1)

    def test_final_week_profit_is_down_against_baseline(self) -> None:
        pnl = f"({activations()['daily_pnl']}) p"
        final, base = KEY["final_week"], KEY["baseline_weeks"]
        (now,) = run_spark(self.db, f"SELECT SUM(profit_ngn) FROM {pnl} WHERE day BETWEEN DATE '{final['start']}' AND DATE '{final['end']}'")[0]
        (before,) = run_spark(self.db, f"SELECT SUM(profit_ngn) / 4 FROM {pnl} WHERE day BETWEEN DATE '{base['start']}' AND DATE '{base['end']}'")[0]
        self.assertLess(now, before)

    def test_compile_is_one_statement_and_rule_targets_transfer_check(self) -> None:
        plan = statements()
        compile_sql = next(s for s in plan if s.startswith("COMPILE USL"))
        self.assertEqual(compile_sql.count("CREATE TABLE"), len(activations()))
        self.assertTrue(plan[-1].startswith("REGISTER DQ transfer_reached_bank TABLE lightning.metastore.becuz.becuz.transfer_check"))


if __name__ == "__main__":
    unittest.main()
