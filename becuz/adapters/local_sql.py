"""Sample-mode warehouse: the same Spark SQL, translated by sqlglot, on in-memory DuckDB.

It builds the becuz USL locally from the very activation queries Zetaris runs,
so sample mode does real work on the scenario CSVs and never replays an answer.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import duckdb
import sqlglot

from base import ledger
from base.tools import is_read_only
from becuz.usl import SOURCES, activations
from data.generator import ROOT

from . import QueryError


def to_duckdb(sql: str) -> str:
    return sqlglot.transpile(sql, read="spark", write="duckdb")[0]


def _value(cell):
    return cell.isoformat(sep=" ") if isinstance(cell, datetime) else cell.isoformat() if isinstance(cell, date) else cell


class LocalWarehouse:
    via = "local"
    usl = "becuz"

    def __init__(self, scenario: str, ledger_path: Path | None = None):
        folder = ROOT / scenario
        if not folder.is_dir():
            raise QueryError(f"unknown scenario: {scenario}")
        self.ledger_path = ledger_path
        self.db = duckdb.connect()
        self.db.execute("SET threads = 1")  # deterministic results run to run
        for source, tables in SOURCES.items():
            self.db.execute(f"CREATE SCHEMA {source}")
            for table in tables:
                path = (folder / f"{table}.csv").as_posix()
                self.db.execute(f"CREATE VIEW {source}.{table} AS SELECT * FROM read_csv_auto('{path}')")
        self.db.execute(f"CREATE SCHEMA {self.usl}")
        for table, sql in activations().items():
            self.db.execute(f"CREATE VIEW {self.usl}.{table} AS {to_duckdb(sql)}")

    def query(self, sql: str) -> list[dict]:
        if not is_read_only(sql):
            raise QueryError("refusing non-read-only SQL")
        try:
            cursor = self.db.execute(to_duckdb(sql))
        except (duckdb.Error, sqlglot.errors.SqlglotError) as exc:
            raise QueryError(str(exc)) from exc
        headers = [column[0] for column in cursor.description]
        rows = [dict(zip(headers, map(_value, row))) for row in cursor.fetchall()]
        ledger.write(self.ledger_path, {"kind": "query", "tool": "query_data", "ok": True, "via": self.via,
                                        "sql": sql[:500], "row_count": len(rows)})
        return rows
