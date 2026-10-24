"""Preflight: four PASS lines (config, zetaris, model, agent) before the first real run."""
from __future__ import annotations

import sys
from dataclasses import replace

from becuz.adapters import warehouse
from becuz.adapters.nightshift import Nightshift
from becuz.config import load
from becuz.investigate import investigate

PASS = "PASS"
FAIL = "FAIL"


def main() -> int:
    config = load()
    checks: list[tuple[str, bool, str]] = []

    config_ok = config.sample_mode or (config.has_zetaris and config.has_nightshift)
    checks.append(("config", config_ok, _config_detail(config)))

    try:
        wh = warehouse(config)
        # A real USL read: proves the agent user can see the USL, and warms Zetaris before a live run.
        found = wh.query(f"SELECT MAX(day) AS last_day FROM {wh.usl}.daily_pnl")
        checks.append(("zetaris", bool(found and found[0]["last_day"]), f"daily_pnl up to {found[0]['last_day']} via={wh.via}"))
    except Exception as exc:
        checks.append(("zetaris", False, str(exc)[:160]))

    if config.sample_mode:
        checks.append(("model", True, "via=sample-rules (sample mode makes no model call)"))
    else:
        try:
            result = Nightshift(config).ask_messages([{"role": "user", "content": "Reply with the single word: ready"}])
            checks.append(("model", bool(result.text.strip()), f"via={result.via} model={result.model}"))
        except Exception as exc:
            checks.append(("model", False, str(exc)[:160]))

    # The whole agent graph on the bundled s01 shop, offline, so this stays quick on any machine.
    try:
        offline = replace(config, sample_mode=True, ledger_path=None, trace_path=None)
        report = investigate({"question": "Why is my profit down?", "scenario": "s01"}, offline)
        causes = len(report["causes"])
        checks.append(("agent", report["status"] == "complete" and causes > 0, f"sample s01: {causes} cause(s) supported"))
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
