from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from base.pipeline import Pipeline
from becuz.adapters import QueryError, warehouse
from becuz.adapters.local_sql import LocalWarehouse
from becuz.adapters.zetaris import ZetarisWarehouse
from becuz.metrics import COMPONENTS, period_totals, profit_tree
from data.generator import ROOT

KEY = json.loads((ROOT / "s01" / "answer_key.json").read_text(encoding="utf-8"))
FINAL = (date.fromisoformat(KEY["final_week"]["start"]), date.fromisoformat(KEY["final_week"]["end"]))


def impact(cause: str) -> float:
    return next(c["impact_ngn"] for c in KEY["causes"] if c["cause_id"] == cause)


class FakePipeline:
    def __init__(self, result: dict):
        self.result = result

    def query(self, sql: str) -> dict:
        return self.result


class LocalWarehouseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wh = LocalWarehouse("s01")
        cls.tree = profit_tree(cls.wh, *FINAL)

    def test_leakage_and_wastage_changes_match_answer_key(self) -> None:
        self.assertAlmostEqual(self.tree["leakage_ngn"]["change"], -impact("transfer_leakage"), delta=1)
        self.assertAlmostEqual(self.tree["wastage_ngn"]["change"], -impact("wastage_spike"), delta=1)

    def test_profit_is_the_tree_identity(self) -> None:
        for side in ("current", "baseline"):
            parts = {c: self.tree[c][side] for c in COMPONENTS}
            expected = parts["net_sales_ngn"] - parts["cogs_ngn"] - parts["wastage_ngn"] - parts["opex_ngn"] - parts["leakage_ngn"]
            self.assertAlmostEqual(parts["profit_ngn"], expected, delta=1)
        self.assertLess(self.tree["profit_ngn"]["change"], 0)

    def test_refuses_writes_before_running(self) -> None:
        with self.assertRaises(QueryError):
            self.wh.query("DROP TABLE becuz.sales")

    def test_bad_sql_is_a_permanent_error(self) -> None:
        with self.assertRaises(QueryError) as caught:
            self.wh.query("SELECT missing_column FROM becuz.sales")
        self.assertFalse(caught.exception.transient)

    def test_period_must_be_real_dates(self) -> None:
        with self.assertRaises(ValueError):
            period_totals(self.wh, "2026-10-12' OR 1=1 --", FINAL[1])
        with self.assertRaises(ValueError):
            period_totals(self.wh, FINAL[1], FINAL[0])

    def test_unknown_scenario_fails_clearly(self) -> None:
        with self.assertRaises(QueryError):
            LocalWarehouse("s99")

    def test_factory_picks_local_in_sample_mode(self) -> None:
        config = SimpleNamespace(sample_mode=True, ledger_path=None)
        self.assertEqual(warehouse(config).via, "local")


class ZetarisWarehouseTests(unittest.TestCase):
    def test_rows_become_dicts_with_numbers(self) -> None:
        raw = {"headers": ["day", "profit_ngn"], "data": [["2026-10-12", "-83580.0"]]}
        wh = ZetarisWarehouse(FakePipeline({"ok": True, "rows": raw["data"], "raw": raw}))
        self.assertEqual(wh.query("SELECT 1"), [{"day": "2026-10-12", "profit_ngn": -83580.0}])

    def test_timeouts_are_transient(self) -> None:
        wh = ZetarisWarehouse(FakePipeline({"ok": False, "error": "zetaris: HTTP 0: The read operation timed out"}))
        with self.assertRaises(QueryError) as caught:
            wh.query("SELECT 1")
        self.assertTrue(caught.exception.transient)

    def test_refusals_are_permanent(self) -> None:
        wh = ZetarisWarehouse(FakePipeline({"ok": False, "error": "zetaris: HTTP 400: not permitted"}))
        with self.assertRaises(QueryError) as caught:
            wh.query("SELECT 1")
        self.assertFalse(caught.exception.transient)

    def test_guard_blocks_writes_before_the_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = SimpleNamespace(sample_mode=False, ledger_path=Path(tmp) / "l.jsonl", nightshift_base_url="",
                                     nightshift_token="", nightshift_model="")
            with self.assertRaises(QueryError) as caught:
                ZetarisWarehouse(Pipeline(config)).query("DROP TABLE x")
        self.assertIn("non-read-only", str(caught.exception))


@unittest.skipUnless(os.getenv("BECUZ_LIVE") == "1", "set BECUZ_LIVE=1 to compare against live Zetaris")
class LiveParityTests(unittest.TestCase):
    def test_zetaris_and_local_agree_on_the_profit_tree(self) -> None:
        from base.config import load

        live = profit_tree(warehouse(load()), *FINAL)
        local = profit_tree(LocalWarehouse("s01"), *FINAL)
        for component in COMPONENTS:
            for side in ("current", "baseline", "change"):
                self.assertAlmostEqual(live[component][side], local[component][side], delta=1, msg=f"{component} {side}")


if __name__ == "__main__":
    unittest.main()
