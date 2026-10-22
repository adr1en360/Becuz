"""Shared runner for admin setup scripts: dry run by default, one statement per call, secrets hidden."""
from __future__ import annotations

import os
import sys

from base.config import load
from base.zetaris import ZetarisClient

HIDDEN = "***"


def hide(text: str, *secrets: str) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, HIDDEN)
    return text


def admin_env(*names: str) -> tuple[ZetarisClient, dict] | None:
    """Load .env and return an admin client plus the named values, or None if any is missing."""
    config = load()  # also loads .env into the environment
    env = {name: os.getenv(name, "").strip() for name in ("ZETARIS_ADMIN_API_KEY", *names)}
    missing = [name for name, value in env.items() if not value or value.startswith("<")]
    if missing:
        print("missing in .env: " + ", ".join(missing), file=sys.stderr)
        return None
    client = ZetarisClient(config.zetaris_rest_url, config.zetaris_org_id, env["ZETARIS_ADMIN_API_KEY"])
    return client, env


def run_plan(client: ZetarisClient, plan: list[str], apply: bool, start: int, secrets: tuple[str, ...]) -> int:
    if not apply:
        for n, sql in enumerate(plan, 1):
            print(f"{n:>2}. {hide(sql, *secrets)}\n")
        print(f"Dry run: {len(plan)} statements, nothing sent. Add --apply to run them.")
        return 0
    for n, sql in enumerate(plan, 1):
        if n < start:
            continue
        try:
            client.run_sql(sql)
        except Exception as exc:  # stop at the first failure so nothing half-runs silently
            print(f"{n:>2}. FAILED: {hide(str(exc), *secrets)[:600]}", file=sys.stderr)
            print(f"Fix the cause, then resume with --apply --start {n}", file=sys.stderr)
            return 1
        print(f"{n:>2}. ok  {hide(sql, *secrets)[:90]}")
    return 0
