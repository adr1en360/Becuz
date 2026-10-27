"""One entry point for an investigation, used by run.py --input and POST /run.

Request JSON: {"question": "...", "period_start": "YYYY-MM-DD" (optional; default the latest days in
the data; "week_start" is still accepted), "days": 1 to 28 (optional, default 7),
"scenario": "s01" (sample mode only)}.
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
from becuz.judge import Judge
from becuz.metrics import MAX_DAYS, NotEnoughHistory
from becuz.orchestration.graph import STEP_LIMIT, build_graph
from becuz.tracing import Trace
from data.generator import SCENARIOS

MAX_QUESTION = 500
REPO = Path(__file__).resolve().parent.parent


class BadRequest(ValueError):
    pass


OUT_OF_SCOPE = ("Becuz explains what happened to your shop's money: profit, sales, costs, expenses and cash. "
                "Try \"Why is my profit down?\", \"How is my shop doing?\" or \"Where did my money go?\"")


def parse(request: dict, sample_mode: bool) -> tuple[str, date | None, int, str | None]:
    if not isinstance(request, dict):
        raise BadRequest("request must be a JSON object")
    question = request.get("question")
    if not isinstance(question, str) or not question.strip() or len(question) > MAX_QUESTION:
        raise BadRequest(f"question must be text of 1 to {MAX_QUESTION} characters")
    if Scout(key=b"scope-check").classify(question)[1] == 0:  # refuse off-topic before any run starts
        raise BadRequest(OUT_OF_SCOPE)
    start = request.get("period_start") or request.get("week_start")
    try:
        start = date.fromisoformat(start) if start else None
    except (TypeError, ValueError):
        raise BadRequest("period_start must be a date like 2026-10-12") from None
    days = request.get("days", 7)
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= MAX_DAYS:
        raise BadRequest(f"days must be a whole number from 1 to {MAX_DAYS}")
    scenario = request.get("scenario", "s01") if sample_mode else None
    if sample_mode and scenario not in SCENARIOS:
        raise BadRequest(f"scenario must be one of {', '.join(SCENARIOS)}")
    return question.strip(), start, days, scenario


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


def new_run_id() -> str:
    return f"inv-{uuid.uuid4().hex[:10]}"


def trace_events(run_id: str, config) -> list[dict] | None:
    """A run's trace events so far, or None if there is no such run. The run ID format is checked first,
    so a request can never name another file."""
    logs = config.trace_path.parent if config.trace_path else None
    if not (logs and isinstance(run_id, str) and re.fullmatch(r"inv-[0-9a-f]{10}", run_id)):
        return None
    path = logs / f"trace-{run_id}.jsonl"
    if not path.exists():
        return None
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def confirm(run_id: str, cause_id: str, config) -> str:
    """The owner confirms a cause from an earlier run; H-MEM stores it so later runs test it first.

    Only a cause the Checker supported in that run can be confirmed.
    """
    lines = trace_events(run_id, config)
    if lines is None:
        raise BadRequest(f"no trace found for run {run_id}")
    if not any(l["agent_name"] == "Checker" and l["action"] == "supported" and l["input_summary"] == cause_id for l in lines):
        raise BadRequest(f"{cause_id} was not a supported cause in run {run_id}")
    spec = CATALOGUE[cause_id]
    memory = open_memory(config.trace_path.parent)  # a trace exists, so the logs folder does
    fact = memory.add(f"{spec.title}. The owner confirmed this cause after run {run_id}.", "owner_confirm",
                      tags=["owner_confirmed", f"cause:{cause_id}", spec.component], agent_id="owner", run_id=run_id)
    memory.add(f"How it was found: {spec.falsified_if} was tested against the records.", "owner_confirm",
               type="procedural", tags=["procedure", f"cause:{cause_id}"], agent_id="owner", run_id=run_id,
               related_to=[fact])
    return fact


def investigate(request: dict, config, run_id: str | None = None) -> dict:
    question, start, days, scenario = parse(request, config.sample_mode)
    run_id = run_id or new_run_id()
    logs = config.trace_path.parent if config.trace_path else None
    trace = Trace(run_id, logs)
    # Every query passes the Scout Intent contract gate; it also counts queries for the report.
    wh = ContractGate(warehouse(config, scenario or "s01"), Scout(log_path=logs / "scout.jsonl" if logs else None))
    run = {"run_id": run_id, "mode": "sample" if config.sample_mode else "live", "scenario": scenario,
           "via": wh.via, "started": time.monotonic(), "queries": lambda: wh.used,
           "trace_file": shown(trace.path)}
    world = WorldModel(log_path=logs / "world.jsonl" if logs else None)  # the shared claims list
    # The Checker's bounded context; its carryover is one summary line, so the spec's minimum budget fits.
    chain = Markovian(run_id, config=ChunkConfig(carryover_tokens=128), log_path=logs / "markovian.jsonl" if logs else None)
    judge = Judge(chain, None if config.sample_mode else Nightshift(config))
    graph = build_graph(wh, trace, run, world, open_memory(logs), judge)
    state = {"question": question, "days": days} | ({"period_start": start} if start else {})
    try:
        return graph.invoke(state, {"recursion_limit": STEP_LIMIT})["report"]
    except ContractRefused as exc:
        if exc.reason == "out-of-scope":
            raise BadRequest(OUT_OF_SCOPE) from None
        raise
    except (NotEnoughHistory, OverflowError) as exc:  # OverflowError: a start date near year 1
        raise BadRequest(f"Not enough records for that period: {exc}. Becuz compares a period with the same days "
                         "in the 4 periods before it.") from None
    finally:
        judge.close()  # a failed run must not leave a rating running in the background
