"""Live warehouse: the becuz USL in Zetaris, reached through Pipeline.query (guard plus ledger)."""
from __future__ import annotations

from base.pipeline import Pipeline
from becuz.usl import USL

from . import QueryError


def _value(cell):
    # Zetaris returns every value as a string; numbers become floats so the critic can compare them.
    if isinstance(cell, str):
        try:
            return float(cell)
        except ValueError:
            return cell
    return cell


class ZetarisWarehouse:
    via = "zetaris"
    usl = USL

    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    def query(self, sql: str) -> list[dict]:
        result = self.pipeline.query(sql)
        if not result.get("ok"):
            error = str(result.get("error", "query failed"))
            # ZetarisError reports network failures and timeouts as HTTP 0.
            raise QueryError(error, transient="HTTP 0:" in error)
        headers = result["raw"].get("headers") or []
        return [dict(zip(headers, map(_value, row))) for row in result["rows"]]
