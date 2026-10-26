"""Where the agent's SQL runs: Zetaris when live, DuckDB over the scenario CSVs in sample mode.

Both take the same Spark SQL, refuse anything but read-only SQL, and return rows as dicts.
Templates name USL tables as `{usl}.<table>`; each warehouse fills in its own prefix.
"""
from __future__ import annotations

import time
from typing import Protocol


class QueryError(RuntimeError):
    """A query failed. `transient` errors (timeouts, network) are worth retrying."""

    def __init__(self, message: str, transient: bool = False):
        super().__init__(message)
        self.transient = transient


class Warehouse(Protocol):
    via: str  # "zetaris" or "local", recorded in traces and receipts
    usl: str  # prefix for USL tables in SQL templates

    def query(self, sql: str) -> list[dict]: ...


class Retrying:
    """Retries one query after a transient failure and reports each retry, so it shows in the trace.
    It waits 2, 4, then 8 seconds between attempts, so a short network drop does not end the run.
    Everything else (via, usl, the contract gate's open and used) passes through to the wrapped warehouse."""

    def __init__(self, wh, on_retry, attempts: int = 4, wait_s: float = 2.0):
        self.wh, self.on_retry, self.attempts, self.wait_s = wh, on_retry, attempts, wait_s

    def __getattr__(self, name):
        return getattr(self.wh, name)

    def query(self, sql: str) -> list[dict]:
        for attempt in range(1, self.attempts + 1):
            try:
                return self.wh.query(sql)
            except QueryError as exc:
                if not exc.transient or attempt == self.attempts:
                    raise
                self.on_retry(attempt, exc)
                time.sleep(self.wait_s * 2 ** (attempt - 1))


def warehouse(config, scenario: str = "s01") -> Warehouse:
    if config.sample_mode:
        from .local_sql import LocalWarehouse

        return LocalWarehouse(scenario, config.ledger_path)
    from .zetaris import ZetarisWarehouse

    return ZetarisWarehouse.from_config(config)
