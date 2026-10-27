from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import duckdb

from becuz.adapters.local_sql import to_duckdb
from becuz.ingest import ingest
from becuz.ingest.profile import profile_column
from becuz.usl import SOURCES, activations
from data.generator import ROOT
from data.reshape import reshape

S01 = ROOT / "s01"


def read(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


class IngestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.upload, cls.out = root / "upload", root / "out"
        reshape(S01, cls.upload)  # s06 built from s01 as it is now
        cls.mapping = ingest(cls.upload, cls.out)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_reshaped_upload_maps_back_to_roles(self) -> None:
        roles = self.mapping["roles"]
        self.assertTrue(self.mapping["ok"], [c for c in self.mapping["checks"] if not c["ok"]])
        self.assertEqual({r: e["file"] for r, e in roles.items() if r not in ("staff", "fx")}, {
            "sale": "sales_export.csv", "sale_line": "items_sold.csv", "product": "items.csv",
            "cost": "purchases.csv", "expense": "spending.csv", "bank_txn": "bank.csv", "promo": "discounts.csv"})
        self.assertEqual(roles["sale"]["columns"]["net_ngn"], "Amount (NGN)")
        self.assertEqual(roles["sale"]["value_maps"]["payment_method"]["Bank Transfer"], "transfer")
        self.assertEqual(roles["bank_txn"]["value_maps"]["channel"]["Bank Charges"], "charge")
        self.assertEqual(roles["bank_txn"]["date_formats"]["posted_at"], "%d/%m/%Y %H:%M")

    def test_canonical_output_reproduces_s01_figures(self) -> None:
        for source in S01.glob("*.csv"):
            if source.stem == "stock_movements":
                continue
            headers, want = read(source)
            got_headers, got = read(self.out / source.name)
            self.assertEqual(got_headers, headers, source.name)
            self.assertEqual(len(got), len(want), source.name)
            for column in headers:
                if column.endswith("_ngn") or column in ("qty", "usd_ngn"):
                    total = lambda rows: round(sum(float(r[column] or 0) for r in rows), 2)  # noqa: E731
                    self.assertEqual(total(got), total(want), f"{source.name}.{column}")

    def test_missing_stock_is_reported(self) -> None:
        self.assertEqual(self.mapping["missing_roles"], {"stock_movement": "your upload has no stock records"})
        headers, rows = read(self.out / "stock_movements.csv")
        self.assertEqual((headers, rows), (read(S01 / "stock_movements.csv")[0], []))

    def test_swapped_amount_columns_are_blocked(self) -> None:
        bad = {**self.mapping, "roles": {**self.mapping["roles"]}}
        sale = bad["roles"]["sale"] = {**bad["roles"]["sale"], "columns": {**bad["roles"]["sale"]["columns"]}}
        sale["columns"]["net_ngn"], sale["columns"]["discount_ngn"] = "Disc", "Amount (NGN)"
        out = Path(self.tmp.name) / "bad"
        result = ingest(self.upload, out, bad)
        failed = {c["check"] for c in result["checks"] if not c["ok"]}
        self.assertFalse(result["ok"])
        self.assertIn("sale_line: lines add up to each sale's net amount", failed)
        self.assertFalse((out / "sales.csv").exists())

    def test_existing_usl_builds_on_the_output(self) -> None:
        def pnl(folder: Path) -> list:
            db = duckdb.connect()
            for source, tables in SOURCES.items():
                db.execute(f"CREATE SCHEMA {source}")
                for table in tables:
                    path = (folder / f"{table}.csv").as_posix()
                    if not read(folder / f"{table}.csv")[1]:  # header only: borrow column types (see report)
                        path = (S01 / f"{table}.csv").as_posix()
                        db.execute(f"CREATE TABLE {source}.{table} AS SELECT * FROM read_csv_auto('{path}') LIMIT 0")
                        continue
                    db.execute(f"CREATE TABLE {source}.{table} AS SELECT * FROM read_csv_auto('{path}')")
            db.execute("CREATE SCHEMA becuz")
            for table, sql in activations().items():
                db.execute(f"CREATE TABLE becuz.{table} AS {to_duckdb(sql)}")
            return db.execute("SELECT ROUND(SUM(net_sales_ngn), 2), ROUND(SUM(cogs_ngn), 2), ROUND(SUM(opex_ngn), 2), "
                              "ROUND(SUM(leakage_ngn), 2), ROUND(SUM(wastage_ngn), 2) FROM becuz.daily_pnl").fetchone()

        got, want = pnl(self.out), pnl(S01)
        self.assertEqual(got[:4], want[:4])
        self.assertEqual(got[4], 0)  # no stock file, so no wastage

    def test_profile_reads_day_first_dates_and_naira_amounts(self) -> None:
        self.assertEqual(profile_column(["24/08/2026", "05/10/2026"])["date_formats"], ["%d/%m/%Y"])
        self.assertEqual(profile_column(["05/10/2026"])["date_formats"], ["%d/%m/%Y", "%m/%d/%Y"])
        self.assertEqual(profile_column(["1,750.50", "₦200", ""])["type"], "number")
        self.assertEqual(profile_column(["2.00", "3"])["type"], "int")  # a whole quantity written with decimals
        self.assertEqual(profile_column(["nan", "1e3"])["type"], "text")


def edited(source: Path, target: Path, name: str, change) -> Path:
    """A copy of an upload with one file's header and rows changed by `change(headers, rows)`."""
    for f in source.glob("*.csv"):
        (target / f.name).write_bytes(f.read_bytes())
    headers, rows = read(target / name)
    headers, rows = change(headers, rows)
    with (target / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, headers)
        writer.writeheader()
        writer.writerows(rows)
    return target


class BadUploadTests(unittest.TestCase):
    """Uploads that look fine but would give wrong answers must be blocked or handled."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        reshape(S01, cls.root / "s06")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def run_ingest(self, name: str, file: str, change) -> dict:
        upload = self.root / name
        upload.mkdir()
        return ingest(edited(self.root / "s06", upload, file, change), self.root / f"{name}-out")

    def failed(self, mapping: dict) -> list[str]:
        return [c["detail"] for c in mapping["checks"] if not c["ok"]]

    def test_an_unknown_payment_type_blocks_with_a_plain_message(self) -> None:
        def wallet(headers, rows):
            rows[0]["Paid Via"] = "Wallet"
            return headers, rows
        mapping = self.run_ingest("wallet", "sales_export.csv", wallet)
        self.assertFalse(mapping["ok"])
        self.assertIn("We don't recognise these payment types: Wallet", self.failed(mapping))

    def test_a_header_only_sales_file_is_blocked(self) -> None:
        mapping = self.run_ingest("empty", "sales_export.csv", lambda headers, rows: (headers, []))
        self.assertFalse(mapping["ok"])

    def test_total_paid_is_taken_as_net_over_total(self) -> None:
        def totals(headers, rows):
            renamed = {"Gross": "Total", "Amount (NGN)": "Total Paid"}
            return [renamed.get(h, h) for h in headers], [{renamed.get(k, k): v for k, v in r.items()} for r in rows]
        mapping = self.run_ingest("totals", "sales_export.csv", totals)
        self.assertEqual(mapping["roles"]["sale"]["columns"]["net_ngn"], "Total Paid")
        self.assertTrue(mapping["ok"], self.failed(mapping))

    def test_invoices_with_a_line_per_product_get_line_ids(self) -> None:
        def one_invoice(headers, rows):
            key = next(h for h in headers if "invoice" in h.lower() and "no" in h.lower())
            for r in rows[:3]:
                r[key] = "INV-SHARED"
            return headers, rows
        mapping = self.run_ingest("lines", "purchases.csv", one_invoice)
        self.assertTrue(mapping["ok"], self.failed(mapping))
        ids = [r["invoice_id"] for r in read(self.root / "lines-out" / "supplier_invoices.csv")[1]]
        self.assertEqual(ids[:3], ["INV-SHARED-1", "INV-SHARED-2", "INV-SHARED-3"])

    def test_a_reviewed_mapping_naming_a_missing_column_is_blocked(self) -> None:
        upload = self.root / "s06"
        mapping = ingest(upload, self.root / "typo-probe")
        mapping["roles"]["sale"]["columns"]["payment_method"] = "Paid Vai"
        mapping.pop("checks"), mapping.pop("ok")
        self.assertFalse(ingest(upload, self.root / "typo-out", mapping)["ok"])


if __name__ == "__main__":
    unittest.main()
