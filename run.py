from __future__ import annotations

import argparse
import json
import sys

from base.config import load
from base.runtime import build_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Becuz")
    parser.add_argument("request", nargs="*")
    parser.add_argument("--sql")
    parser.add_argument("--full", action="store_true", help="print the full query response")
    parser.add_argument("--trace", action="store_true", help="print the agent trace")
    args = parser.parse_args()

    request = args.sql or " ".join(args.request)
    if not request:
        print('usage: python run.py "SELECT 1 AS one"')
        return 2

    agent = build_agent(load())
    result = agent.run(request)

    trace = result.get("trace", [])
    result = {key: value for key, value in result.items() if key != "trace"}

    if not result.get("ok") or args.full or result.get("tool") != "query_data":
        output = result
    else:
        output = _preview(result)
    if args.trace:
        output = {**output, "trace": trace}

    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0 if result.get("ok") else 1


def _preview(result: dict) -> dict:
    rows = result.get("rows") or []
    return {
        "ok": result.get("ok"),
        "tool": result.get("tool"),
        "sql": result.get("sql"),
        "row_count": len(rows),
        "sample": result.get("sample", False),
        "preview": [_short_row(row) for row in rows[:3]],
    }


def _short_row(row):
    if isinstance(row, list):
        return [_short(value) for value in row]
    if isinstance(row, dict):
        return {key: _short(value) for key, value in row.items()}
    return [_short(row)]


def _short(value) -> str:
    text = str(value)
    return text[:160] + ("..." if len(text) > 160 else "")


if __name__ == "__main__":
    sys.exit(main())
