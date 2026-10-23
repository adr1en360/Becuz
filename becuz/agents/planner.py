"""Planner: picks the week, splits the profit change, and orders the causes to test."""
from __future__ import annotations

from datetime import date, timedelta

from becuz.adapters import Warehouse
from becuz.catalogue import CATALOGUE
from becuz.engines.scout_intent import ContractRefused
from becuz.metrics import profit_tree
from becuz.orchestration.state import InvestigationState
from becuz.tracing import Trace


def latest_week(wh: Warehouse) -> tuple[date, date]:
    last = wh.query(f"SELECT MAX(day) AS last_day FROM {wh.usl}.daily_pnl")[0]["last_day"]
    end = date.fromisoformat(str(last)[:10])
    return end - timedelta(days=6), end


def profit_effects(tree: dict) -> dict[str, float]:
    """Each component's effect on profit: sales count up, costs count down."""
    effects = {name.removesuffix("_ngn"): node["change"] for name, node in tree.items() if name != "profit_ngn"}
    return {name: (change if name == "net_sales" else -change) for name, change in effects.items()}


def make_planner(wh: Warehouse, trace: Trace):
    def planner(state: InvestigationState) -> dict:
        # Intake: Scout Intent reads the question and signs the contract every later query must fit.
        contract = wh.open(state["question"], trace.run_id)
        intent = contract["intent"]
        trace.emit("Planner", "scout_contract", state["question"],
                   f"{intent['primary']} (confidence {intent['confidence']:.2f}), contract {contract['contractId']}, "
                   f"{len(contract['scope']['capabilities'])} tables, {contract['scope']['budget']['queriesMax']} queries max",
                   confidence=intent["confidence"], engine="scout_intent")
        if intent["confidence"] == 0:
            raise ContractRefused("out-of-scope")
        start = state.get("week_start")
        start, end = latest_week(wh) if start is None else (start, start + timedelta(days=6))
        tree = profit_tree(wh, start, end)
        effects = profit_effects(tree)
        # Dynamic delegation: causes on the components that lost most are tested first.
        queue = sorted(CATALOGUE, key=lambda cause: effects[CATALOGUE[cause].component])
        trace.emit("Planner", "plan", state["question"],
                   f"profit change {tree['profit_ngn']['change']:+,.0f} for {start}..{end}; testing {', '.join(queue)}",
                   target_agent="Investigator")
        return {"week_start": start, "week_end": end, "tree": tree, "queue": queue, "current": None}

    return planner
