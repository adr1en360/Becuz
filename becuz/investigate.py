"""One entry point for an investigation, used by run.py --input and POST /run.

Request JSON: {"question": "...", "week_start": "YYYY-MM-DD" (optional, a Monday-to-Sunday
week; default the latest week in the data), "scenario": "s01" (sample mode only)}.
"""
from __future__ import annotations

import time
import uuid
from datetime import date
from pathlib import Path

from becuz.adapters import warehouse
from becuz.orchestration.graph import STEP_LIMIT, build_graph
from becuz.tracing import Trace
from data.generator import SCENARIOS

MAX_QUESTION = 500
REPO = Path(__file__).resolve().parent.parent


class BadRequest(ValueError):
    pass


class Counted:
    """Counts queries for the report's stats without changing the warehouse."""

    def __init__(self, wh):
        self.wh, self.via, self.usl, self.count = wh, wh.via, wh.usl, 0

    def query(self, sql: str) -> list[dict]:
        self.count += 1
        return self.wh.query(sql)


def parse(request: dict, sample_mode: bool) -> tuple[str, date | None, str | None]:
    if not isinstance(request, dict):
        raise BadRequest("request must be a JSON object")
    question = request.get("question")
    if not isinstance(question, str) or not question.strip() or len(question) > MAX_QUESTION:
        raise BadRequest(f"question must be text of 1 to {MAX_QUESTION} characters")
    week_start = request.get("week_start")
    try:
        week_start = date.fromisoformat(week_start) if week_start else None
    except (TypeError, ValueError):
        raise BadRequest("week_start must be a date like 2026-10-12") from None
    scenario = request.get("scenario", "s01") if sample_mode else None
    if sample_mode and scenario not in SCENARIOS:
        raise BadRequest(f"scenario must be one of {', '.join(SCENARIOS)}")
    return question.strip(), week_start, scenario


def shown(path) -> str:
    """The trace path relative to the repo, so reports never expose a local folder."""
    if not path:
        return ""
    try:
        return Path(path).relative_to(REPO).as_posix()
    except ValueError:
        return Path(path).name


def investigate(request: dict, config) -> dict:
    question, week_start, scenario = parse(request, config.sample_mode)
    run_id = f"inv-{uuid.uuid4().hex[:10]}"
    wh = Counted(warehouse(config, scenario or "s01"))
    trace = Trace(run_id, config.trace_path.parent if config.trace_path else None)
    run = {"run_id": run_id, "mode": "sample" if config.sample_mode else "live", "scenario": scenario,
           "via": wh.via, "started": time.monotonic(), "queries": lambda: wh.count,
           "trace_file": shown(trace.path)}
    graph = build_graph(wh, trace, run)
    state = {"question": question} | ({"week_start": week_start} if week_start else {})
    return graph.invoke(state, {"recursion_limit": STEP_LIMIT})["report"]
