"""Register a scenario's S3 CSVs in Zetaris as four Lightning sources.

Uses the ADMIN key: these statements create objects, so the agent's read-only
path (Pipeline.query and its guard) is deliberately not used here.

    uv run python -m scripts.zetaris_setup s01            # dry run: print statements, keys hidden
    uv run python -m scripts.zetaris_setup s01 --apply    # run them, one statement per call
"""
from __future__ import annotations

import argparse
import sys

from base.zetaris import rows
from becuz.usl import SOURCES
from scripts.admin import admin_env, hide, run_plan

DESCRIPTIONS = {
    "pos_files": "Becuz synthetic POS records",
    "bank_files": "Becuz synthetic bank statement",
    "books_files": "Becuz synthetic supplier invoices and expenses",
    "context_files": "Becuz synthetic exchange rates",
}


def statements(scenario: str, bucket: str, key_id: str, secret: str) -> list[str]:
    creds = f'awsAccessKeyId "{key_id}", awsSecretAccessKey "{secret}"'
    out = []
    for source, tables in SOURCES.items():
        out.append(f'CREATE LIGHTNING DATABASE {source} DESCRIBE BY "{DESCRIPTIONS[source]}"')
        for table in tables:
            out.append(
                f"CREATE LIGHTNING FILESTORE TABLE {table} FROM {source} FORMAT CSV OPTIONS ("
                f'path "s3a://{bucket}/becuz/{scenario}/{table}.csv", {creds}, '
                f'header "true", inferSchema "true", delimiter ",")'
            )
    return out


def checks() -> list[str]:
    return [f"SELECT COUNT(*) AS n FROM {source}.{table}" for source, tables in SOURCES.items() for table in tables]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("scenario")
    parser.add_argument("--apply", action="store_true", help="run the statements against Zetaris")
    parser.add_argument("--start", type=int, default=1, help="resume at this statement number")
    args = parser.parse_args()

    loaded = admin_env("S3_BUCKET", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
    if loaded is None:
        return 1
    admin, env = loaded
    secrets = (env["AWS_ACCESS_KEY_ID"], env["AWS_SECRET_ACCESS_KEY"], env["ZETARIS_ADMIN_API_KEY"])
    plan = statements(args.scenario, env["S3_BUCKET"], env["AWS_ACCESS_KEY_ID"], env["AWS_SECRET_ACCESS_KEY"])
    failed = run_plan(admin, plan, args.apply, args.start, secrets)
    if failed or not args.apply:
        return failed
    for sql in checks():
        try:
            count = rows(admin.run_sql(sql))[0][0]
            print(f"check {sql.split('FROM ')[1]}: {count} rows")
        except Exception as exc:
            print(f"check {sql}: FAILED {hide(str(exc), *secrets)[:200]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
