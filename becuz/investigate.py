"""One entry point for an investigation, used by run.py --input and POST /run.

Request JSON: {"question": "...", "week_start": "YYYY-MM-DD" (optional, a Monday-to-Sunday
week; default the latest week in the data), "scenario": "s01" (sample mode only)}.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from datetime import date
from pathlib import Path

from becuz.adapters import warehouse
from becuz.adapters.nightshift import Nightshift
from becuz.catalogue import CATALOGUE
from becuz.engines.hmem import HMEM
from becuz.engines.scout_intent import ContractGate, ContractRefused, Scout
from becuz.engines.markovian import ChunkConfig, Markovian
from becuz.engines.world_model import WorldModel
from becuz.judge import NightshiftJudge, RulesJudge
from becuz.orchestration.graph import STEP_LIMIT, build_graph
from becuz.tracing import Trace
from data.generator import SCENARIOS

MAX_QUESTION = 500
REPO = Path(__file__).resolve().parent.parent


class BadRequest(ValueError):
    pass


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


def open_memory(logs: Path | None) -> HMEM:
    return HMEM(path=logs / "hmem.json" if logs else None, ledger_path=logs / "hmem.jsonl" if logs else None)


def confirm(run_id: str, cause_id: str, config) -> str:
    """The owner confirms a cause from an earlier run; H-MEM stores it so later runs test it first.

    Only a cause the Checker supported in that run can be confirmed.
    """
    logs = config.trace_path.parent if config.trace_path else None
    trace_file = logs / f"trace-{run_id}.jsonl" if logs and re.fullmatch(r"inv-[0-9a-f]{10}", run_id) else None
    if not trace_file or not trace_file.exists():
        raise BadRequest(f"no trace found for run {run_id}")
    lines = [json.loads(line) for line in trace_file.read_text(encoding="utf-8").splitlines()]
    if not any(l["agent_name"] == "Checker" and l["action"] == "supported" and l["input_summary"] == cause_id for l in lines):
        raise BadRequest(f"{cause_id} was not a supported cause in run {run_id}")
    spec = CATALOGUE[cause_id]
    memory = open_memory(logs)
    fact = memory.add(f"{spec.title}. The owner confirmed this cause after run {run_id}.", "owner_confirm",
                      tags=["owner_confirmed", f"cause:{cause_id}", spec.component], agent_id="owner", run_id=run_id)
    memory.add(f"How it was found: {spec.falsified_if} was tested against the records.", "owner_confirm",
               type="procedural", tags=["procedure", f"cause:{cause_id}"], agent_id="owner", run_id=run_id,
               related_to=[fact])
    return fact


def investigate(request: dict, config) -> dict:
    question, week_start, scenario = parse(request, config.sample_mode)
    run_id = f"inv-{uuid.uuid4().hex[:10]}"
    logs = config.trace_path.parent if config.trace_path else None
    trace = Trace(run_id, logs)
    # Every query passes the Scout Intent contract gate; it also counts queries for the report.
    wh = ContractGate(warehouse(config, scenario or "s01"), Scout(log_path=logs / "scout.jsonl" if logs else None))
    run = {"run_id": run_id, "mode": "sample" if config.sample_mode else "live", "scenario": scenario,
           "via": wh.via, "started": time.monotonic(), "queries": lambda: wh.used,
           "trace_file": shown(trace.path)}
    world = WorldModel(log_path=logs / "world.jsonl" if logs else None)  # the shared claims list
    judge = RulesJudge() if config.sample_mode else NightshiftJudge(Nightshift(config))
    # The Checker's bounded context; its carryover is one summary line, so the spec's minimum budget fits.
    chain = Markovian(run_id, config=ChunkConfig(carryover_tokens=128), log_path=logs / "markovian.jsonl" if logs else None)
    graph = build_graph(wh, trace, run, world, open_memory(logs), chain, judge)
    state = {"question": question} | ({"week_start": week_start} if week_start else {})
    try:
        return graph.invoke(state, {"recursion_limit": STEP_LIMIT})["report"]
    except ContractRefused as exc:
        if exc.reason == "out-of-scope":
            raise BadRequest("Becuz answers questions about why your profit changed") from None
        raise
