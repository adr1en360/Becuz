"""The investigation graph: Planner -> Investigator <-> Checker -> Writer.

The Checker sends a claim back to the Investigator (at most twice) or marks it,
then routes to the next cause or to the Writer. A transient Zetaris failure retries
only the query that failed, and each retry is written to the trace by the agent that hit it.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from becuz.adapters import Retrying, Warehouse
from becuz.agents.checker import make_checker, make_router
from becuz.agents.investigator import make_investigator
from becuz.agents.planner import make_planner
from becuz.agents.writer import make_writer
from becuz.engines.hmem import HMEM
from becuz.engines.world_model import WorldModel
from becuz.judge import Judge
from becuz.orchestration.state import InvestigationState
from becuz.tracing import Trace

STEP_LIMIT = 60  # planner + 6 causes x (investigate + check) x up to 3 attempts + writer, with room to spare


def build_graph(wh: Warehouse, trace: Trace, run: dict, world: WorldModel, memory: HMEM, judge: Judge):
    def retrying(agent: str) -> Retrying:
        return Retrying(wh, lambda attempt, exc: trace.emit(
            agent, "retry_query", f"attempt {attempt} failed", str(exc)[:160], retry_count=attempt,
            status="retrying", via=wh.via))

    graph = StateGraph(InvestigationState)
    graph.add_node("planner", make_planner(retrying("Planner"), trace, memory))
    graph.add_node("investigator", make_investigator(retrying("Investigator"), trace, world))
    graph.add_node("checker", make_checker(retrying("Checker"), trace, world, memory, judge))
    graph.add_node("writer", make_writer(wh, trace, run, world, judge))
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "investigator")
    graph.add_edge("investigator", "checker")
    graph.add_conditional_edges("checker", make_router(world), ["investigator", "writer"])
    graph.add_edge("writer", END)
    return graph.compile()
