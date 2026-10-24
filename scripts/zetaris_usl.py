"""Build the Becuz USL (Unified Semantic Layer) over the registered shop sources.

The USL declares the shop's tables and keys once; Zetaris turns every key into a
data-quality rule. Two derived tables do work inside Zetaris: transfer_check
(each transfer sale with its matching bank credit, if any) and daily_pnl (the
profit tree per day). The agent reads only these USL tables.

    uv run python -m scripts.zetaris_usl            # dry run: print statements
    uv run python -m scripts.zetaris_usl --apply    # run them, one statement per call
    uv run python -m scripts.zetaris_usl --table daily_pnl            # dry run: re-activate one table
    uv run python -m scripts.zetaris_usl --table daily_pnl --apply    # after its query changed
"""
from __future__ import annotations

import argparse

from becuz.usl import DDL, NAMESPACE, USL, activations
from scripts.admin import admin_env, run_plan


def activate(table: str, sql: str) -> str:
    return f"ACTIVATE USL TABLE {USL}.{table} AS\n{sql}"


def statements() -> list[str]:
    plan = [
        "CREATE NAMESPACE IF NOT EXISTS lightning.metastore",
        f"CREATE NAMESPACE IF NOT EXISTS {NAMESPACE}",
        # One call: a multi-table COMPILE must not be split at semicolons.
        f"COMPILE USL IF NOT EXISTS becuz DEPLOY NAMESPACE {NAMESPACE} DDL{DDL}",
    ]
    plan += [activate(table, sql) for table, sql in activations().items()]
    plan.append(f"REGISTER DQ transfer_reached_bank TABLE {USL}.transfer_check AS bank_txn_id IS NOT NULL")
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="run the statements against Zetaris")
    parser.add_argument("--start", type=int, default=1, help="resume at this statement number")
    parser.add_argument("--table", choices=sorted(activations()), help="only re-activate this USL table")
    args = parser.parse_args()
    loaded = admin_env()
    if loaded is None:
        return 1
    admin, env = loaded
    plan = [activate(args.table, activations()[args.table])] if args.table else statements()
    return run_plan(admin, plan, args.apply, args.start, (env["ZETARIS_ADMIN_API_KEY"],))


if __name__ == "__main__":
    raise SystemExit(main())
