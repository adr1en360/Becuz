"""The investigation graph: Planner -> Investigator <-> Checker -> Writer.

The Checker sends a claim back to the Investigator (at most twice) or marks it,
then routes to the next cause or to the Writer. Transient Zetaris failures are
retried by LangGraph's RetryPolicy, not by hand-written loops.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from becuz.adapters import QueryError, Warehouse
from becuz.agents.checker import make_checker, make_router
from becuz.agents.investigator import make_investigator
from becuz.agents.planner import make_planner
from becuz.agents.writer import make_writer
from becuz.engines.hmem import HMEM
from becuz.engines.markovian import Markovian
from becuz.engines.world_model import WorldModel
from becuz.orchestration.state import InvestigationState
from becuz.tracing import Trace

RETRY = RetryPolicy(max_attempts=3, retry_on=lambda exc: isinstance(exc, QueryError) and exc.transient)
STEP_LIMIT = 60  # planner + 6 causes x (investigate + check) x up to 3 attempts + writer, with room to spare


def build_graph(wh: Warehouse, trace: Trace, run: dict, world: WorldModel, memory: HMEM, chain: Markovian, judge):
    graph = StateGraph(InvestigationState)
    graph.add_node("planner", make_planner(wh, trace, memory), retry_policy=RETRY)
    graph.add_node("investigator", make_investigator(wh, trace, world), retry_policy=RETRY)
    graph.add_node("checker", make_checker(wh, trace, world, memory, chain, judge), retry_policy=RETRY)
    graph.add_node("writer", make_writer(wh, trace, run, world, chain, judge))
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "investigator")
    graph.add_edge("investigator", "checker")
    graph.add_conditional_edges("checker", make_router(world), ["investigator", "writer"])
    graph.add_edge("writer", END)
    return graph.compile()
