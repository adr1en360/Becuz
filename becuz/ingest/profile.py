"""Column profiling for an uploaded CSV: type, null rate, distinct ratio, samples, date formats."""
from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

# Day-first before month-first: Nigerian exports write 24/08/2026. A column that fits both is a tie,
# noted in the mapping, and resolved day-first.
DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y %I:%M %p", "%d/%m/%Y", "%d/%m/%y %H:%M", "%d/%m/%y", "%d-%m-%Y",
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y",
    "%d-%b-%Y %H:%M", "%d-%b-%Y", "%d %b %Y",
]
BOOLS = {"true": True, "false": False, "yes": True, "no": False, "y": True, "n": False}
MONEY_JUNK = re.compile(r"[₦,\s]|NGN|N(?=\d)", re.IGNORECASE)


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:  # Excel on Windows saves "CSV" as cp1252
        text = path.read_text(encoding="cp1252")
    reader = csv.DictReader(text.splitlines())
    headers = list(reader.fieldnames or [])
    repeated = sorted({h for h in headers if headers.count(h) > 1})
    if repeated:  # DictReader would silently keep only the last of them
        raise ValueError(f"{path.name} has the same column name more than once: {', '.join(repeated)}")
    return headers, list(reader)


def parse_number(text: str) -> float | None:
    """'1,750.00', '₦1750', '(200)' -> float; '' -> None; raises ValueError on anything else."""
    text = MONEY_JUNK.sub("", text.strip())
    if not text:
        return None
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    if not re.fullmatch(r"-?\d+(\.\d+)?", text):  # float() would also take 'nan', 'inf' and '1e3'
        raise ValueError(f"not a number: {text!r}")
    return float(text)


def parse_date(text: str, fmt: str) -> datetime | None:
    text = text.strip()
    return datetime.strptime(text, fmt) if text else None


def _all(values: list[str], parse) -> bool:
    try:
        for value in values:
            parse(value)
    except ValueError:
        return False
    return True


def profile_column(values: list[str]) -> dict:
    filled = [v.strip() for v in values if v.strip()]
    distinct = sorted(set(filled))
    formats = [f for f in DATE_FORMATS if filled and _all(filled, lambda v, f=f: datetime.strptime(v, f))]
    if not filled:
        kind = "empty"
    elif all(v.lower() in BOOLS for v in filled):
        kind = "bool"
    elif formats:
        kind = "date"
    elif _all(filled, lambda v: parse_number(v).is_integer() or int("x")):  # '2.00' is a whole number
        kind = "int"
    elif _all(filled, parse_number):
        kind = "number"
    else:
        kind = "text"
    return {
        "type": kind,
        "null_rate": round(1 - len(filled) / len(values), 4) if values else 1.0,
        "distinct_ratio": round(len(distinct) / len(filled), 4) if filled else 0.0,
        "samples": filled[:5],
        "values": distinct if len(distinct) <= 30 else None,
        "date_formats": formats,
    }


def profile_file(path: Path) -> dict:
    headers, rows = read_csv(path)
    return {"file": path.name, "rows": len(rows),
            "columns": {h: profile_column([r.get(h) or "" for r in rows]) for h in headers}}


def profile_dir(folder: Path) -> dict[str, dict]:
    return {p.name: profile_file(p) for p in sorted(folder.glob("*.csv"))}
