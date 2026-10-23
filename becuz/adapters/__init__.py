"""Where the agent's SQL runs: Zetaris when live, DuckDB over the scenario CSVs in sample mode.

Both take the same Spark SQL, refuse anything but read-only SQL, and return rows as dicts.
Templates name USL tables as `{usl}.<table>`; each warehouse fills in its own prefix.
"""
from __future__ import annotations

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


def warehouse(config, scenario: str = "s01") -> Warehouse:
    if config.sample_mode:
        from .local_sql import LocalWarehouse

        return LocalWarehouse(scenario, config.ledger_path)
    from .zetaris import ZetarisWarehouse

    return ZetarisWarehouse.from_config(config)
