"""Scorecard: runs every test week in sample mode and scores what Becuz found against its answer key.

The agent never reads answer_key.json; only this scorecard does. For each week it counts the planted
causes found (as a profit cause or a cash gap), the planted causes missed, findings that were not planted,
the red herrings ruled out, and whether each found impact is within the key's tolerance.

    uv run python -m becuz.eval            # table
    uv run python -m becuz.eval --json     # the same numbers as JSON
"""
from __future__ import annotations

import json
import sys
from types import SimpleNamespace

from becuz.investigate import investigate
from data.generator import ROOT, SCENARIOS

QUESTION = "Why is my profit down this week?"


def score(scenario: str) -> dict:
    key = json.loads((ROOT / scenario / "answer_key.json").read_text(encoding="utf-8"))
    config = SimpleNamespace(sample_mode=True, ledger_path=None, trace_path=None)
    report = investigate({"question": QUESTION, "scenario": scenario}, config)
    found = {c["cause_id"]: c["impact_ngn"] for c in report["causes"] + report["cash_gaps"]}
    planted = {c["cause_id"]: c["impact_ngn"] for c in key["causes"]}
    ruled_out = {r["cause_id"] for r in report["ruled_out"]}
    within = [c for c in planted if c in found
              and abs(found[c] - planted[c]) <= abs(planted[c]) * key["tolerance_pct"] / 100]
    return {"scenario": scenario, "planted": len(planted), "found": len(planted.keys() & found.keys()),
            "missed": sorted(planted.keys() - found.keys()), "not_planted": sorted(found.keys() - planted.keys()),
            "red_herrings": len(key["red_herrings"]),
            "red_herrings_ruled_out": len(set(key["red_herrings"]) & ruled_out),
            "impact_within_tolerance": len(within), "tolerance_pct": key["tolerance_pct"]}


def main() -> int:
    rows = [score(s) for s in SCENARIOS]
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=2))
        return 0
    print(f"{'week':6} {'found':>9} {'impact ok':>10} {'herrings out':>13}  not planted")
    for r in rows:
        print(f"{r['scenario']:6} {r['found']:>4} of {r['planted']:<2} {r['impact_within_tolerance']:>6} of {r['found']:<2}"
              f" {r['red_herrings_ruled_out']:>8} of {r['red_herrings']:<2}  {', '.join(r['not_planted']) or '-'}")
    planted, found = sum(r["planted"] for r in rows), sum(r["found"] for r in rows)
    herrings, out = sum(r["red_herrings"] for r in rows), sum(r["red_herrings_ruled_out"] for r in rows)
    print(f"total  {found} of {planted} planted causes found; {out} of {herrings} red herrings ruled out; "
          f"{sum(len(r['not_planted']) for r in rows)} finding(s) not planted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
