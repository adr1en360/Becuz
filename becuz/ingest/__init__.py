"""Shape-agnostic ingest: profile an upload, map it onto canonical roles, prove it, write canonical CSVs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .mapping import canonical, cell, columns_of, map_upload
from .profile import profile_dir
from .reconcile import check


def ingest(upload: Path, out: Path, mapping: dict | None = None) -> dict:
    """Map (or apply a reviewed mapping), reconcile, and write mapping.json plus the canonical CSVs.

    Canonical CSVs are written only when every check passes; mapping.json is always written for review.
    """
    mapping = mapping or map_upload(profile_dir(upload))
    tables, errors = canonical(mapping, upload)
    mapping["checks"] = check(mapping, tables, errors)
    mapping["ok"] = all(c["ok"] for c in mapping["checks"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "mapping.json").write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    if mapping["ok"]:
        for table in tables:
            with (out / f"{table}.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(columns_of(table))
                writer.writerows([cell(r[c]) for c in columns_of(table)] for r in tables[table])
    return mapping
