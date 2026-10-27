"""Writer: builds the Investigation from the supported claims only.

Every number is computed here from the profit tree and the claims; the schema's
validators then re-check that they add up. Profit causes explain the profit change;
cash gaps (money the till recorded that never reached the bank) are reported apart,
because the sale still counts as profit. The owner-facing wording comes from the
templates below; the Checker's model judgement supplies each finding's confidence and note.
"""
from __future__ import annotations

import time

from becuz.adapters import Warehouse
from becuz.agents.checker import record_judgements
from becuz.agents.planner import profit_effects
from becuz.catalogue import CATALOGUE
from becuz.metrics import baseline_days
from becuz.engines.world_model import WorldModel
from becuz.judge import Judge
from becuz.orchestration.state import InvestigationState, period
from becuz.schemas import MIN_EFFECT_NGN, Investigation
from becuz.tracing import Trace
from becuz.words import baseline_words, naira, plural, span


def pct(part: float, whole: float) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def node_status(effect: float, explained: float) -> str:
    if abs(effect) < MIN_EFFECT_NGN:
        return "no_change"
    if not explained:
        return "unexplained"
    return "explained" if abs(effect - explained) <= 0.1 * abs(effect) else "partly_explained"


def what_happened(profit: dict, direction: str, when: str) -> str:
    if direction == "flat":
        return f"Profit {when} was {naira(profit['current'])}, about the same as usual."
    side = "less" if direction == "down" else "more"
    return (f"Profit {when} was {naira(profit['current'])}, which is {naira(profit['change'])} {side} "
            f"than usual ({naira(profit['baseline'])}).")


def outcome_line(profit: dict, causes: list[dict], cash: list[dict], period: str, when: str) -> str:
    """What acting on the findings is worth, from the measured figures only: no forecast, no new number."""
    missing = sum(c["effect_ngn"] for c in cash)
    chase = (f"chasing the {plural(sum(len(c['row_ids']) for c in cash), 'missing transfer')} brings "
             f"{naira(missing)} back into your account") if cash else ""
    if causes:
        fixed = profit["current"] - sum(c["effect_ngn"] for c in causes)
        these = "this cause" if len(causes) == 1 else f"these {plural(len(causes), 'cause')}"
        line = (f"Without {these}, {period} would have made about {naira(fixed)}, "
                f"against {naira(profit['baseline'])} usually")
        return f"{line}, and {chase}." if chase else f"{line}."
    if chase:
        return f"Profit is on track; {chase}."
    return f"Nothing to fix {when}."


def cash_line(claim: dict) -> str:
    return (f"{naira(claim['effect_ngn'])} from {plural(len(claim['row_ids']), 'transfer sale')} was recorded at the till "
            "but never reached the bank. The sales still count toward your profit, but this money is missing "
            "from your account.")


def recall_message(cause_id: str, held_again: bool | None, when: str) -> str:
    title = CATALOGUE[cause_id].title
    opening = f"You confirmed that {title[0].lower()}{title[1:]} after an earlier run, so Becuz checked it first this time."
    if held_again is None:
        return f"{opening} The records {when} could not check it."
    if held_again:
        return f"{opening} It happened again {when}."
    return f"{opening} It did not happen {when}, so Becuz will rely on that memory less until you confirm it again."


def assemble(state: InvestigationState, run: dict, world: WorldModel, judge: Judge) -> Investigation:
    tree = state["tree"]
    start, end = state["period_start"], state["period_end"]
    baseline = baseline_days(start, end)
    span_noun, when = span(start, end)
    profit = tree["profit_ngn"]
    change = profit["change"]
    claims = world.claims_by_cause(period(state)).values()
    # The Writer may only use what the World Model hands it: the claims the Checker supported.
    supported = sorted(world.context_for("writer")["claims"], key=lambda c: c["effect_ngn"])
    cash = [c for c in supported if CATALOGUE[c["cause_id"]].component == "cash"]
    causes_found = [c for c in supported if c not in cash]
    effects = profit_effects(tree)
    explained_by = {name: sum(c["effect_ngn"] for c in causes_found if CATALOGUE[c["cause_id"]].component == name)
                    for name in effects}
    explained = sum(c["effect_ngn"] for c in causes_found)
    # A missing model rating does not undo a SQL verdict, so the run stays complete; the raw error is in the trace.
    unrated = sum("error" in c.get("judgement", {}) for c in claims)

    def evidence(claim: dict) -> dict:
        spec = CATALOGUE[claim["cause_id"]]
        return {"evidence_id": f"ev-{claim['cause_id']}", "table": f"becuz.{spec.table}", "sql": claim["effect_sql"],
                "row_ids": claim["row_ids"], "value_ngn": claim["effect_ngn"],
                "summary": f"{spec.title}: {claim['effect_ngn']:+,.0f}", "via": run["via"],
                "check": {"match": claim["check"]["match"], "rerun_value_ngn": claim["check"]["rerun_value_ngn"],
                          "note": f"{claim['reason']} {claim['judgement']['note']}",
                          "model": claim["judgement"]["model"], "via": claim["judgement"]["via"],
                          "signed": claim["judgement"]["signed"]}}

    def finding(claim: dict) -> dict:
        spec = CATALOGUE[claim["cause_id"]]
        return {"cause_id": claim["cause_id"], "title": spec.title, "impact_ngn": claim["effect_ngn"],
                "impact_evidence_id": f"ev-{claim['cause_id']}", "confidence": claim["judgement"]["confidence"],
                "evidence": [evidence(claim)],
                "falsified_by": [{"test": spec.falsified_if, "evidence_id": f"ev-{claim['cause_id']}", "survived": True}],
                "depends_on_sources": list(spec.sources), "retries": claim["retries"]}

    causes = [{
        **finding(c), "component": CATALOGUE[c["cause_id"]].component, "share_of_change_pct": pct(c["effect_ngn"], change),
        "rank": rank, "origin": CATALOGUE[c["cause_id"]].origin, "nature": CATALOGUE[c["cause_id"]].nature,
        "counterfactual_ngn": round(profit["current"] - c["effect_ngn"], 2),
    } for rank, c in enumerate(causes_found, start=1)]

    owner_questions = [{
        "cause_id": c["cause_id"],
        "question": f"{plural(len(c['row_ids']), 'transfer sale')} {when} {'has' if len(c['row_ids']) == 1 else 'have'} no matching payment in the bank "
                    f"({', '.join(c['row_ids'][:6])}). Can you check them with the staff who recorded them?",
    } for c in cash]

    direction = "down" if change <= -MIN_EFFECT_NGN else "up" if change >= MIN_EFFECT_NGN else "flat"
    why = [f"{CATALOGUE[c['cause_id']].title}. This cost you {naira(c['effect_ngn'])}." for c in causes_found]
    if not why and state.get("answer"):  # a direct question: no causes were tested, so say how to get them
        why = ['Ask "Why is my profit down?" for the causes behind the change.']
    if not why:
        why = [{"flat": "Nothing changed enough to need an explanation.",
                "up": f"Profit went up, and none of the problems Becuz checks for showed up {when}.",
                "down": "None of the causes Becuz checked explains this drop."}[direction]]
    data = {
        "answer": state.get("answer"),
        "run_id": run["run_id"], "status": "complete", "errors": [], "mode": run["mode"], "synthetic": True, "scenario": run["scenario"],
        "frame": {"question": state["question"], "period_start": start, "period_end": end,
                  "days": (end - start).days + 1, "baseline_start": baseline[0], "baseline_end": baseline[-1],
                  "baseline": baseline_words(start, end)},
        "headline": {"current_ngn": profit["current"], "baseline_ngn": profit["baseline"], "change_ngn": change,
                     "change_pct": pct(change, abs(profit["baseline"])) if profit["baseline"] else None,
                     "direction": direction},
        "tree": [{"component": name, "current_ngn": tree[f"{name}_ngn"]["current"],
                  "baseline_ngn": tree[f"{name}_ngn"]["baseline"], "change_ngn": tree[f"{name}_ngn"]["change"],
                  "profit_effect_ngn": effect, "share_of_change_pct": pct(effect, change),
                  "status": node_status(effect, explained_by[name])} for name, effect in effects.items()],
        "causes": causes,
        "cash_gaps": [finding(c) for c in cash],
        "memory": [{"cause_id": c["cause_id"], **{k: v for k, v in c["recall"].items() if k != "memory_id"},
                    "message": recall_message(c["cause_id"], c["recall"]["held_again"], when)}
                   for c in claims if "recall" in c],
        "ruled_out": [{"cause_id": c["cause_id"], "hypothesis": CATALOGUE[c["cause_id"]].title, "reason": c["reason"],
                       "tested_value_ngn": c["effect_ngn"], "evidence_id": None}
                      for c in claims if c["status"] == "rejected"],
        "not_tested": [f"{c['cause_id']}: {c['reason']}" for c in claims if c["status"] == "not_tested"],
        "convergence": {"explained_ngn": round(explained, 2), "explained_pct": pct(explained, change),
                        "unexplained_ngn": round(change - explained, 2)},
        "summary": {
            "what_happened": what_happened(profit, direction, when),
            "why": why,
            "cash": [cash_line(c) for c in cash],
            "outcome": "" if state.get("answer") else outcome_line(profit, causes_found, cash, span_noun, when),
            "what_to_do": [{"cause_id": c["cause_id"], "action": CATALOGUE[c["cause_id"]].action} for c in causes_found + cash],
        },
        "owner_questions": owner_questions,
        "limitations": ["Findings show correlation, not proven causation.",
                        "The shop data is synthetic.",
                        judge.limitation]
                       + ([f"The model could not rate {unrated} of {len(claims)} causes; their SQL checks still stand."]
                          if unrated else []),
        "stats": {"duration_s": round(time.monotonic() - run["started"], 2), "zetaris_queries": run["queries"](),
                  "model_calls": judge.calls, "retries": sum(c["retries"] for c in claims),
                  "models": dict(judge.models), "via": {run["via"]: run["queries"](), judge.via: judge.reviews}},
        "trace_file": run["trace_file"],
    }
    return Investigation.model_validate(data)


def make_writer(wh: Warehouse, trace: Trace, run: dict, world: WorldModel, judge: Judge):
    def writer(state: InvestigationState) -> dict:
        record_judgements(judge, world, trace, period(state))
        efficiency = judge.finish()
        trace.emit("Checker", "markovian_summary", f"{efficiency['chunks']} reviews",
                   f"{efficiency['totalTokensUsed']} tokens used, {efficiency['totalTokensSaved']} saved "
                   f"({efficiency['efficiencyPercent']}%, {efficiency['tokenLabel']})", engine="markovian")
        report = assemble(state, run, world, judge)
        trace.emit("Writer", "write_report", f"{len(world.claims())} claims from the World Model",
                   f"{plural(len(report.causes), 'profit cause')}, {plural(len(report.cash_gaps), 'cash gap')}, {len(report.ruled_out)} ruled out, "
                   f"{report.convergence.explained_pct}% of the profit change explained", plain="Writing your answer.")
        return {"report": report.model_dump(mode="json")}

    return writer
