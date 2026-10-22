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
        sql = f"""
        WITH cost AS (
          SELECT AVG(CASE WHEN invoice_date BETWEEN '{BASELINE[0]}' AND '{BASELINE[1]}' THEN CAST(unit_cost_ngn AS DOUBLE) END) AS base,
                 AVG(CASE WHEN invoice_date BETWEEN '{FINAL[0]}' AND '{FINAL[1]}' THEN CAST(unit_cost_ngn AS DOUBLE) END) AS final
          FROM supplier_invoices WHERE product_id = 'P001'),
        sold AS (
          SELECT SUM(CAST(l.qty AS INT)) AS qty FROM sale_lines l JOIN sales s ON s.sale_id = l.sale_id
          WHERE l.product_id = 'P001' AND CAST(s.sold_at AS DATE) BETWEEN '{FINAL[0]}' AND '{FINAL[1]}')
        SELECT -sold.qty * (cost.final - cost.base) FROM cost, sold"""
        self.assertAlmostEqual(self.scalar(sql), self.impact("supplier_cost_rise"), delta=1)

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


if __name__ == "__main__":
    unittest.main()
