"""Planner: picks the week, splits the profit change, and orders the causes to test."""
from __future__ import annotations

from datetime import date, timedelta

from becuz.adapters import Warehouse
from becuz.catalogue import CATALOGUE
from becuz.engines.hmem import HMEM
from becuz.engines.scout_intent import ContractRefused
from becuz.metrics import profit_tree
from becuz.orchestration.state import InvestigationState
from becuz.tracing import Trace
from becuz.words import naira, plural


def latest_week(wh: Warehouse) -> tuple[date, date]:
    last = wh.query(f"SELECT MAX(day) AS last_day FROM {wh.usl}.daily_pnl")[0]["last_day"]
    end = date.fromisoformat(str(last)[:10])
    return end - timedelta(days=6), end


def profit_effects(tree: dict) -> dict[str, float]:
    """Each component's effect on profit: sales count up, costs count down."""
    effects = {name.removesuffix("_ngn"): node["change"] for name, node in tree.items() if name != "profit_ngn"}
    return {name: (change if name == "net_sales" else -change) for name, change in effects.items()}


def recall_confirmed(memory: HMEM, question: str) -> dict[str, str]:
    """Causes the owner confirmed in earlier runs, best match first: cause_id -> memory id."""
    recalled = {}
    for hit in memory.query(question, tags=["owner_confirmed"])["results"]:
        cause = next(t.removeprefix("cause:") for t in hit["memory"]["tags"] if t.startswith("cause:"))
        recalled.setdefault(cause, hit["memory"]["id"])
    return recalled


def make_planner(wh: Warehouse, trace: Trace, memory: HMEM):
    def planner(state: InvestigationState) -> dict:
        # Intake: Scout Intent reads the question and signs the contract every later query must fit.
        contract = wh.open(state["question"], trace.run_id)
        intent = contract["intent"]
        trace.emit("Planner", "scout_contract", state["question"],
                   f"{intent['primary']} (confidence {intent['confidence']:.2f}), contract {contract['contractId']}, "
                   f"{len(contract['scope']['capabilities'])} tables, {contract['scope']['budget']['queriesMax']} queries max",
                   confidence=intent["confidence"], engine="scout_intent", plain="Reading your question.")
        if intent["confidence"] == 0:
            raise ContractRefused("out-of-scope")
        start = state.get("week_start")
        start, end = latest_week(wh) if start is None else (start, start + timedelta(days=6))
        tree = profit_tree(wh, start, end)
        effects = profit_effects(tree)
        # H-MEM: causes the owner confirmed before are tested first; then the components that lost most.
        recalled = recall_confirmed(memory, state["question"])
        trace.emit("Planner", "recall", state["question"],
                   f"{len(recalled)} owner-confirmed causes recalled: {', '.join(recalled) or 'none'}", engine="hmem",
                   plain=f"Remembered {plural(len(recalled), 'cause')} you confirmed before; checking first." if recalled
                   else "Nothing confirmed before, so every cause gets a fresh look.")
        # A cash cause has no profit node, so it sorts as no profit effect.
        queue = sorted(CATALOGUE, key=lambda cause: (cause not in recalled, effects.get(CATALOGUE[cause].component, 0.0)))
        trace.emit("Planner", "plan", state["question"],
                   f"profit change {tree['profit_ngn']['change']:+,.0f} for {start}..{end}; testing {', '.join(queue)}",
                   target_agent="Investigator",
                   plain=f"Profit this week is {naira(tree['profit_ngn']['change'])} "
                         f"{'below' if tree['profit_ngn']['change'] < 0 else 'above'} a usual week. "
                         f"Checking {plural(len(queue), 'possible cause')}.")
        return {"week_start": start, "week_end": end, "tree": tree, "queue": queue, "current": None, "recalled": recalled}

    return planner
