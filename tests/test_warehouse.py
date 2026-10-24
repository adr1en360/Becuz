from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from becuz.adapters import QueryError, warehouse
from becuz.adapters.local_sql import LocalWarehouse
from becuz.adapters.zetaris import ZetarisError, ZetarisWarehouse
from becuz.metrics import COMPONENTS, profit_tree
from data.generator import ROOT

KEY = json.loads((ROOT / "s01" / "answer_key.json").read_text(encoding="utf-8"))
FINAL = (date.fromisoformat(KEY["final_week"]["start"]), date.fromisoformat(KEY["final_week"]["end"]))


def impact(cause: str) -> float:
    return next(c["impact_ngn"] for c in KEY["causes"] if c["cause_id"] == cause)


class FakeClient:
    def __init__(self, result=None, error: ZetarisError | None = None):
        self.result, self.error, self.sent = result, error, []

    def run_sql(self, sql: str) -> dict:
        self.sent.append(sql)
        if self.error:
            raise self.error
        return self.result


class LocalWarehouseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wh = LocalWarehouse("s01")
        cls.tree = profit_tree(cls.wh, *FINAL)

    def test_wastage_change_matches_answer_key(self) -> None:
        self.assertAlmostEqual(self.tree["wastage_ngn"]["change"], -impact("wastage_spike"), delta=1)

    def test_profit_is_the_tree_identity(self) -> None:
        for side in ("current", "baseline"):
            parts = {c: self.tree[c][side] for c in COMPONENTS}
            # Missing transfers are a cash gap, not a cost, so they are not in the identity.
            expected = parts["net_sales_ngn"] - parts["cogs_ngn"] - parts["wastage_ngn"] - parts["opex_ngn"]
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
            profit_tree(self.wh, "2026-10-12' OR 1=1 --", FINAL[1])
        with self.assertRaises(ValueError):
            profit_tree(self.wh, FINAL[1], FINAL[0])
        with self.assertRaises(ValueError):  # not a 7-day week
            profit_tree(self.wh, FINAL[0], date(2026, 10, 14))

    def test_a_week_without_data_fails_instead_of_reading_zero(self) -> None:
        with self.assertRaises(ValueError):
            profit_tree(self.wh, date(2027, 1, 4), date(2027, 1, 10))

    def test_unknown_scenario_fails_clearly(self) -> None:
        with self.assertRaises(QueryError):
            LocalWarehouse("s99")

    def test_factory_picks_local_in_sample_mode(self) -> None:
        config = SimpleNamespace(sample_mode=True, ledger_path=None)
        self.assertEqual(warehouse(config).via, "local")


class ZetarisWarehouseTests(unittest.TestCase):
    def test_rows_become_dicts_with_numbers(self) -> None:
        raw = {"headers": ["day", "profit_ngn"], "data": [["2026-10-12", "-83580.0"]]}
        client = FakeClient(raw)
        self.assertEqual(ZetarisWarehouse(client).query("SELECT 1;;"), [{"day": "2026-10-12", "profit_ngn": -83580.0}])
        self.assertEqual(client.sent, ["SELECT 1"])  # trailing semicolons are never sent

    def test_timeouts_are_transient(self) -> None:
        wh = ZetarisWarehouse(FakeClient(error=ZetarisError(0, "The read operation timed out")))
        with self.assertRaises(QueryError) as caught:
            wh.query("SELECT 1")
        self.assertTrue(caught.exception.transient)

    def test_refusals_are_permanent(self) -> None:
        wh = ZetarisWarehouse(FakeClient(error=ZetarisError(400, "not permitted")))
        with self.assertRaises(QueryError) as caught:
            wh.query("SELECT 1")
        self.assertFalse(caught.exception.transient)

    def test_a_failed_result_set_is_retried_like_a_timeout(self) -> None:
        wh = ZetarisWarehouse(FakeClient(error=ZetarisError(400, '{"msg":"Could not create ResultSet: null"}')))
        with self.assertRaises(QueryError) as caught:
            wh.query("SELECT 1")
        self.assertTrue(caught.exception.transient)

    def test_guard_blocks_writes_before_the_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient({})
            with self.assertRaises(QueryError) as caught:
                ZetarisWarehouse(client, Path(tmp) / "l.jsonl").query("DROP TABLE x")
        self.assertIn("non-read-only", str(caught.exception))
        self.assertEqual(client.sent, [])


@unittest.skipUnless(os.getenv("BECUZ_LIVE") == "1", "set BECUZ_LIVE=1 to compare against live Zetaris")
class LiveParityTests(unittest.TestCase):
    def test_zetaris_and_local_agree_on_the_profit_tree(self) -> None:
        from becuz.config import load

        live = profit_tree(warehouse(load()), *FINAL)
        local = profit_tree(LocalWarehouse("s01"), *FINAL)
        for component in COMPONENTS:
            for side in ("current", "baseline", "change"):
                self.assertAlmostEqual(live[component][side], local[component][side], delta=1, msg=f"{component} {side}")


if __name__ == "__main__":
    unittest.main()
