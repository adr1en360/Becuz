"""Writer: builds the Investigation from the supported claims only.

Every number is computed here from the profit tree and the claims; the schema's
validators then re-check that they add up. The wording comes from fixed templates
until the Nightshift model steps are connected.
"""
from __future__ import annotations

import time

from becuz.adapters import Warehouse
from becuz.agents.planner import profit_effects
from becuz.catalogue import CATALOGUE
from becuz.metrics import week
from becuz.engines.world_model import WorldModel
from becuz.orchestration.state import InvestigationState, period
from becuz.schemas import MIN_EFFECT_NGN, Investigation
from becuz.tracing import Trace


def pct(part: float, whole: float) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def node_status(effect: float, explained: float) -> str:
    if abs(effect) < MIN_EFFECT_NGN:
        return "no_change"
    if not explained:
        return "unexplained"
    return "explained" if abs(effect - explained) <= 0.1 * abs(effect) else "partly_explained"


def assemble(state: InvestigationState, run: dict, world: WorldModel) -> Investigation:
    tree = state["tree"]
    baseline = week(state["week_start"], state["week_end"])
    profit = tree["profit_ngn"]
    change = profit["change"]
    claims = world.claims_by_cause(period(state)).values()
    # The Writer may only use what the World Model hands it: the claims the Checker supported.
    supported = sorted(world.context_for("writer")["claims"], key=lambda c: c["effect_ngn"])
    effects = profit_effects(tree)
    explained_by = {name: sum(c["effect_ngn"] for c in supported if CATALOGUE[c["cause_id"]].component == name)
                    for name in effects}
    explained = sum(c["effect_ngn"] for c in supported)

    def evidence(claim: dict) -> dict:
        spec = CATALOGUE[claim["cause_id"]]
        return {"evidence_id": f"ev-{claim['cause_id']}", "table": f"becuz.{spec.table}", "sql": claim["effect_sql"],
                "row_ids": claim["row_ids"], "value_ngn": claim["effect_ngn"],
                "summary": f"{spec.title}: {claim['effect_ngn']:+,.0f}", "via": run["via"],
                "check": {"match": claim["check"]["match"], "rerun_value_ngn": claim["check"]["rerun_value_ngn"],
                          "note": claim["reason"], "via": "rules"}}

    causes = [{
        "cause_id": c["cause_id"], "title": CATALOGUE[c["cause_id"]].title, "component": CATALOGUE[c["cause_id"]].component,
        "impact_ngn": c["effect_ngn"], "impact_evidence_id": f"ev-{c['cause_id']}",
        "share_of_change_pct": pct(c["effect_ngn"], change), "rank": rank,
        "origin": CATALOGUE[c["cause_id"]].origin, "nature": CATALOGUE[c["cause_id"]].nature,
        "confidence": 1.0, "evidence": [evidence(c)],
        "falsified_by": [{"test": CATALOGUE[c["cause_id"]].falsified_if, "evidence_id": f"ev-{c['cause_id']}",
                          "survived": True}],
        "counterfactual_ngn": round(profit["current"] - c["effect_ngn"], 2),
        "depends_on_sources": list(CATALOGUE[c["cause_id"]].sources), "retries": c["retries"],
    } for rank, c in enumerate(supported, start=1)]

    owner_questions = [{
        "cause_id": c["cause_id"],
        "question": f"{len(c['row_ids'])} transfer sales have no matching bank credit ({', '.join(c['row_ids'][:6])}). "
                    "Can you check them with the staff who recorded them?",
    } for c in supported if c["cause_id"] == "transfer_leakage"]

    direction = "down" if change <= -1 else "up" if change >= 1 else "flat"
    data = {
        "run_id": run["run_id"], "status": "complete", "mode": run["mode"], "synthetic": True, "scenario": run["scenario"],
        "frame": {"question": state["question"], "period_start": state["week_start"], "period_end": state["week_end"],
                  "baseline_start": baseline[0], "baseline_end": baseline[1]},
        "headline": {"current_ngn": profit["current"], "baseline_ngn": profit["baseline"], "change_ngn": change,
                     "change_pct": pct(change, abs(profit["baseline"])) if profit["baseline"] else None,
                     "direction": direction},
        "tree": [{"component": name, "current_ngn": tree[f"{name}_ngn"]["current"],
                  "baseline_ngn": tree[f"{name}_ngn"]["baseline"], "change_ngn": tree[f"{name}_ngn"]["change"],
                  "profit_effect_ngn": effect, "share_of_change_pct": pct(effect, change),
                  "status": node_status(effect, explained_by[name])} for name, effect in effects.items()],
        "causes": causes,
        "ruled_out": [{"cause_id": c["cause_id"], "hypothesis": CATALOGUE[c["cause_id"]].title, "reason": c["reason"],
                       "tested_value_ngn": c["effect_ngn"], "evidence_id": None}
                      for c in claims if c["status"] == "rejected"],
        "not_tested": [f"{c['cause_id']}: {c['reason']}" for c in claims if c["status"] == "not_tested"],
        "convergence": {"explained_ngn": round(explained, 2), "explained_pct": pct(explained, change),
                        "unexplained_ngn": round(change - explained, 2)},
        "summary": {
            "what_happened": f"Profit this week was {profit['current']:,.0f} against a usual week of "
                             f"{profit['baseline']:,.0f}, {direction} {abs(change):,.0f}.",
            "why": [f"{CATALOGUE[c['cause_id']].title}: {c['effect_ngn']:+,.0f}" for c in supported]
                   or ["None of the tested causes explains the change."],
            "what_to_do": [{"cause_id": c["cause_id"], "action": CATALOGUE[c["cause_id"]].action} for c in supported],
        },
        "owner_questions": owner_questions,
        "limitations": ["Findings show correlation, not proven causation.",
                        "The shop data is synthetic.",
                        "The report wording comes from fixed templates; every number comes from SQL."],
        "stats": {"duration_s": round(time.monotonic() - run["started"], 2), "zetaris_queries": run["queries"](),
                  "model_calls": 0, "retries": sum(c["retries"] for c in claims), "models": {},
                  "via": {run["via"]: run["queries"](), "rules": 1}},
        "trace_file": run["trace_file"],
    }
    return Investigation.model_validate(data)


def make_writer(wh: Warehouse, trace: Trace, run: dict, world: WorldModel):
    def writer(state: InvestigationState) -> dict:
        report = assemble(state, run, world)
        trace.emit("Writer", "write_report", f"{len(world.claims())} claims from the World Model",
                   f"{len(report.causes)} supported, {len(report.ruled_out)} ruled out, "
                   f"{report.convergence.explained_pct}% of the change explained")
        return {"report": report.model_dump(mode="json")}

    return writer
