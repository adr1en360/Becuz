from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb

from data.generator import ROOT, generate

FINAL = ("2026-10-12", "2026-10-18")
BASELINE = ("2026-09-14", "2026-10-11")


class GeneratorTests(unittest.TestCase):
    """Checks one scenario; subclasses below repeat every check for the other scenarios."""

    SCENARIO = "s01"

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / cls.SCENARIO
        cls.key = generate(cls.SCENARIO, cls.out)
        cls.db = duckdb.connect()
        for csv in cls.out.glob("*.csv"):
            cls.db.execute(f"CREATE VIEW {csv.stem} AS SELECT * FROM read_csv_auto('{csv.as_posix()}', all_varchar=true)")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.close()
        cls.tmp.cleanup()

    def scalar(self, sql: str) -> float:
        return float(self.db.execute(sql).fetchone()[0] or 0)

    def impact(self, cause: str) -> float:
        # A cause that was not planted must measure as zero.
        return next((c["impact_ngn"] for c in self.key["causes"] if c["cause_id"] == cause), 0.0)

    def test_same_seed_is_byte_identical_across_processes(self) -> None:
        if self.SCENARIO != "s01":
            self.skipTest("one scenario is enough: every scenario shares the same code path")
        # A fresh interpreter catches ordering that depends on hash seeding.
        with tempfile.TemporaryDirectory() as other:
            code = f"from pathlib import Path; from data.generator import generate; generate('{self.SCENARIO}', Path(r'{other}'))"
            subprocess.run([sys.executable, "-c", code], check=True, cwd=ROOT.parent.parent)
            for path in self.out.iterdir():
                self.assertEqual(path.read_bytes(), (Path(other) / path.name).read_bytes(), path.name)

    def test_supplier_cost_rise_matches_sql(self) -> None:
        # Each sale line is costed at the latest invoice on or before its day (cost in force).
        sql = f"""
        WITH lines AS (
          SELECT CAST(s.sold_at AS DATE) AS day, CAST(l.qty AS INT) AS qty,
                 (SELECT CAST(i.unit_cost_ngn AS DOUBLE) FROM supplier_invoices i
                  WHERE i.product_id = 'P001' AND CAST(i.invoice_date AS DATE) <= CAST(s.sold_at AS DATE)
                  ORDER BY CAST(i.invoice_date AS DATE) DESC LIMIT 1) AS cost
          FROM sale_lines l JOIN sales s ON s.sale_id = l.sale_id WHERE l.product_id = 'P001'),
        f AS (SELECT SUM(qty * cost) AS cost, SUM(qty) AS qty FROM lines WHERE day BETWEEN '{FINAL[0]}' AND '{FINAL[1]}'),
        b AS (SELECT SUM(qty * cost) / SUM(qty) AS unit FROM lines WHERE day BETWEEN '{BASELINE[0]}' AND '{BASELINE[1]}')
        SELECT -(f.cost - f.qty * b.unit) FROM f, b"""
        self.assertAlmostEqual(self.scalar(sql), self.impact("supplier_cost_rise"), delta=1)

    def test_history_is_26_weeks_ending_on_the_final_day(self) -> None:
        days = self.db.execute("SELECT MIN(CAST(cal_date AS DATE)), MAX(CAST(cal_date AS DATE)), COUNT(*) FROM calendar").fetchone()
        self.assertEqual([d.isoformat() for d in days[:2]] + [days[2]], ["2026-04-20", FINAL[1], 182])
        self.assertEqual(self.key["history"], {"start": "2026-04-20", "end": FINAL[1]})

    def test_costs_are_not_all_booked_on_monday(self) -> None:
        # Day-to-day spend and deliveries land on several weekdays; monthly items carry a cover period.
        for table, column in (("expenses", "expense_date"), ("supplier_invoices", "invoice_date")):
            weekdays = self.scalar(f"SELECT COUNT(DISTINCT dayofweek(CAST({column} AS DATE))) FROM {table}")
            self.assertGreaterEqual(weekdays, 6, table)
        uncovered = self.db.execute("""SELECT DISTINCT category FROM expenses
            WHERE category IN ('rent', 'salary', 'levy') AND (cover_start IS NULL OR cover_end IS NULL)""").fetchall()
        self.assertEqual(uncovered, [])
        covered = self.scalar("""SELECT COUNT(*) FROM expenses
            WHERE category IN ('diesel', 'transport', 'electricity') AND cover_start IS NOT NULL""")
        self.assertEqual(covered, 0)
        diesel = self.db.execute("""SELECT MIN(n), MAX(n) FROM (SELECT date_trunc('week', CAST(expense_date AS DATE)) w, COUNT(*) n
            FROM expenses WHERE category = 'diesel' GROUP BY w)""").fetchone()
        self.assertTrue(2 <= diesel[0] <= diesel[1] <= 4, diesel)

    def test_every_product_has_a_cost_from_the_first_day(self) -> None:
        missing = self.scalar("""SELECT COUNT(*) FROM products p WHERE NOT EXISTS (
            SELECT 1 FROM supplier_invoices i WHERE i.product_id = p.product_id AND i.invoice_date = '2026-04-20')""")
        self.assertEqual(missing, 0)

    def test_scenario_stays_small(self) -> None:
        size = sum(path.stat().st_size for path in self.out.iterdir())
        self.assertLess(size, 15_000_000)

    def test_promo_overrun_matches_sql(self) -> None:
        sql = """
        SELECT -SUM(CAST(l.discount_ngn AS DOUBLE)) FROM sale_lines l
        JOIN sales s ON s.sale_id = l.sale_id JOIN promos p ON p.promo_id = l.promo_id
        WHERE CAST(s.sold_at AS DATE) > CAST(p.end_date AS DATE)"""
        self.assertAlmostEqual(self.scalar(sql), self.impact("promo_overrun"), delta=1)

    def test_wastage_spike_matches_sql(self) -> None:
        value = "SUM(CAST(qty AS INT) * CAST(unit_cost_ngn AS DOUBLE))"
        where = "type IN ('expired', 'damaged') AND CAST(moved_at AS DATE) BETWEEN"
        final = self.scalar(f"SELECT {value} FROM stock_movements WHERE {where} '{FINAL[0]}' AND '{FINAL[1]}'")
        base = self.scalar(f"SELECT {value} FROM stock_movements WHERE {where} '{BASELINE[0]}' AND '{BASELINE[1]}'")
        self.assertAlmostEqual(-(final - base / 4), self.impact("wastage_spike"), delta=1)

    def test_transfer_leakage_matches_cross_source_sql(self) -> None:
        unmatched = self.db.execute("""
            SELECT s.sale_id, CAST(s.net_ngn AS DOUBLE) FROM sales s
            LEFT JOIN bank_statement b ON b.ref = s.transfer_ref AND b.channel = 'transfer'
            WHERE s.payment_method = 'transfer' AND b.txn_id IS NULL ORDER BY s.sale_id""").fetchall()
        self.assertEqual([sale for sale, _ in unmatched], self.key["leaked_sale_ids"])
        self.assertAlmostEqual(-sum(net for _, net in unmatched), self.impact("transfer_leakage"), delta=1)
        if self.key["leaked_sale_ids"]:
            staff = self.db.execute(f"""SELECT DISTINCT staff_id FROM sales
                WHERE sale_id IN ({','.join(repr(s) for s in self.key['leaked_sale_ids'])})""").fetchall()
            self.assertEqual(staff, [("ST01",)])

    def test_pos_charges_are_flat(self) -> None:
        rates = self.db.execute("""
            SELECT ROUND(SUM(CASE WHEN channel = 'charge' THEN CAST(amount_ngn AS DOUBLE) END)
                       / SUM(CASE WHEN channel = 'pos_settlement' THEN CAST(amount_ngn AS DOUBLE) END), 4)
            FROM bank_statement WHERE ref LIKE 'POS-%' GROUP BY ref""").fetchall()
        self.assertEqual({rate for (rate,) in rates}, {0.005})
        self.assertIn("pos_charge_rise", self.key["red_herrings"])

    def test_causes_are_ranked_by_impact(self) -> None:
        impacts = [c["impact_ngn"] for c in self.key["causes"]]
        self.assertEqual(impacts, sorted(impacts))
        self.assertTrue(all(i < 0 for i in impacts))
        self.assertTrue(json.loads((self.out / "answer_key.json").read_text())["synthetic"])


class S02Tests(GeneratorTests):
    SCENARIO = "s02"


class S03Tests(GeneratorTests):
    SCENARIO = "s03"


class S04Tests(GeneratorTests):
    SCENARIO = "s04"

    def test_sales_did_not_fall(self) -> None:
        # The planted red herring: "sales fell" must be false in this week.
        total = "SELECT SUM(CAST(net_ngn AS DOUBLE)) FROM sales WHERE CAST(sold_at AS DATE) BETWEEN"
        final = self.scalar(f"{total} '{FINAL[0]}' AND '{FINAL[1]}'")
        base = self.scalar(f"{total} '{BASELINE[0]}' AND '{BASELINE[1]}'") / 4
        self.assertGreaterEqual(final, base)
        self.assertIn("sales_volume_drop", self.key["red_herrings"])


class S05Tests(GeneratorTests):
    SCENARIO = "s05"

    def test_nothing_is_planted(self) -> None:
        self.assertEqual(self.key["causes"], [])



class ScorecardTests(unittest.TestCase):
    def test_the_scorecard_finds_every_planted_cause_and_rules_out_every_red_herring(self) -> None:
        from becuz.eval import score

        for scenario in ("s01", "s04", "s05"):
            with self.subTest(scenario=scenario):
                row = score(scenario)
                self.assertEqual((row["found"], row["missed"]), (row["planted"], []))
                self.assertEqual(row["red_herrings_ruled_out"], row["red_herrings"])
                self.assertEqual(row["impact_within_tolerance"], row["found"])


if __name__ == "__main__":
    unittest.main()
