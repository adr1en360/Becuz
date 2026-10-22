from __future__ import annotations

import sys

from base.config import load
from base.pipeline import Pipeline
from base.runtime import build_agent

PASS = "PASS"
FAIL = "FAIL"


def main() -> int:
    config = load()
    checks: list[tuple[str, bool, str]] = []

    config_ok = config.sample_mode or (
        config.has_zetaris and config.has_nightshift
    )
    checks.append(("config", config_ok, _config_detail(config)))

    pipeline = Pipeline(config)
    try:
        response = pipeline.query("SELECT 1 AS one")
        found = response.get("rows") or []
        ok = bool(response.get("ok")) and bool(found)
        detail = f"{len(found)} row(s)" + (" sample" if config.sample_mode else "")
        checks.append(("zetaris", ok, detail))
    except Exception as exc:
        checks.append(("zetaris", False, str(exc)[:160]))

    try:
        result = pipeline.ask("Reply with the single word: ready")
        checks.append(
            ("model", bool(result.text.strip()), f"via={result.via} model={result.model}")
        )
    except Exception as exc:
        checks.append(("model", False, str(exc)[:160]))

    try:
        agent_result = build_agent(config).run("SELECT 1 AS one")
        ok = bool(agent_result.get("ok")) and int(agent_result.get("steps") or 0) >= 1
        checks.append(
            (
                "agent",
                ok,
                f"tool={agent_result.get('tool')} steps={agent_result.get('steps')}",
            )
        )
    except Exception as exc:
        checks.append(("agent", False, str(exc)[:160]))

    width = max(len(name) for name, _, _ in checks)
    for name, ok, detail in checks:
        print(f"{name:<{width}}  {(PASS if ok else FAIL):<4}  {detail}")
    return 0 if all(ok for _, ok, _ in checks) else 1


def _config_detail(config) -> str:
    parts = [
        "zetaris=" + ("ok" if config.has_zetaris else "missing"),
        "nightshift=" + ("ok" if config.has_nightshift else "missing"),
    ]
    if config.sample_mode:
        parts.append("sample=on")
    return " ".join(parts)


if __name__ == "__main__":
    sys.exit(main())
