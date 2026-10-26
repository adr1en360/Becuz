"""The agents recover on real sample data when one query misbehaves once: the Checker sends a
mismatched claim back for a re-test, and a transient warehouse failure retries only that query.
Both recoveries must show in the trace."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from becuz.adapters import QueryError
from becuz.adapters.local_sql import LocalWarehouse
from becuz.investigate import investigate


class OnceWrong:
    """Real sample warehouse; the first query containing `marker` misbehaves once via `wrong`."""

    def __init__(self, scenario: str, marker: str, wrong):
        self.real, self.marker, self.wrong, self.done = LocalWarehouse(scenario), marker, wrong, False
        self.via, self.usl = self.real.via, self.real.usl

    def query(self, sql: str) -> list[dict]:
        rows = self.real.query(sql)
        if not self.done and self.marker in sql:
            self.done = True
            return self.wrong(rows)
        return rows


def run(wh) -> tuple[dict, list[dict]]:
    with tempfile.TemporaryDirectory() as tmp:
        config = SimpleNamespace(sample_mode=True, ledger_path=None, trace_path=Path(tmp) / "trace.jsonl")
        with patch("becuz.investigate.warehouse", return_value=wh):
            report = investigate({"question": "Why is my profit down this week?", "scenario": "s01"}, config)
        trace = [json.loads(line) for line in (Path(tmp) / report["trace_file"]).read_text(encoding="utf-8").splitlines()]
    return report, trace


class RecoveryTests(unittest.TestCase):
    def test_a_mismatched_claim_is_sent_back_retested_and_then_supported(self) -> None:
        # The Investigator's first measurement of the supplier cause comes back 500 naira off.
        wh = OnceWrong("s01", "final_cost - c.base_cost", lambda rows: [{"effect_ngn": rows[0]["effect_ngn"] - 500}])
        report, trace = run(wh)
        checks = [(l["action"], l["retry_count"]) for l in trace
                  if l["agent_name"] == "Checker" and l["input_summary"] == "supplier_cost_rise" and l["action"] != "judge"]
        self.assertEqual(checks, [("sent_back", 1), ("supported", 1)])
        retest = [l for l in trace if l["agent_name"] == "Investigator" and l["input_summary"] == "supplier_cost_rise"]
        self.assertEqual([l["retry_count"] for l in retest], [0, 1])
        cause = next(c for c in report["causes"] if c["cause_id"] == "supplier_cost_rise")
        self.assertEqual((cause["impact_ngn"], cause["retries"], report["stats"]["retries"]), (-46992.0, 1, 1))

    def test_a_transient_failure_retries_only_that_query_and_is_traced(self) -> None:
        def timeout(rows):
            raise QueryError("zetaris: HTTP 0: The read operation timed out", transient=True)

        with patch("becuz.adapters.time.sleep") as wait:
            report, trace = run(OnceWrong("s01", "transfer_check", timeout))
        wait.assert_called_once_with(10.0)
        (retry,) = [l for l in trace if l["action"] == "retry_query"]
        self.assertEqual((retry["agent_name"], retry["retry_count"], retry["status"]), ("Investigator", 1, "retrying"))
        self.assertEqual([c["cause_id"] for c in report["cash_gaps"]], ["transfer_leakage"])
        self.assertEqual(report["status"], "complete")


if __name__ == "__main__":
    unittest.main()
