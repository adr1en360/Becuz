from __future__ import annotations

import argparse
import json
import sys

from becuz.adapters import QueryError
from becuz.adapters.nightshift import ProviderError
from becuz.config import load
from becuz.investigate import BadRequest, confirm, investigate


def main() -> int:
    parser = argparse.ArgumentParser(description="Becuz: explain why a shop's weekly profit moved")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="run an investigation from a JSON request file")
    group.add_argument("--confirm", nargs=2, metavar=("RUN_ID", "CAUSE_ID"), help="confirm a cause from a past run")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # reports carry the naira sign; Windows consoles default to cp1252

    if args.confirm:
        try:
            print(f"remembered as {confirm(*args.confirm, load())}")
        except (BadRequest, KeyError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0
    try:
        with open(args.input, encoding="utf-8") as handle:
            report = investigate(json.load(handle), load())
    except (OSError, json.JSONDecodeError, BadRequest) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (QueryError, ProviderError) as exc:
        print(f"error: {exc}\nCheck .env and the connections with `uv run python smoke.py`, "
              "or run offline with SAMPLE_MODE=1.", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
