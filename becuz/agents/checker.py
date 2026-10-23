"""Checker: re-runs each claim's SQL itself and supports, rejects or sends it back.

No claim reaches the report unless the re-run matches, the effect is a real loss
of at least MIN_EFFECT_NGN, and record IDs back it. Verdicts are written to the
World Model as new status edges, so the claim's history is kept.
"""
from __future__ import annotations

from typing import Literal

from becuz.adapters import Warehouse
from becuz.catalogue import measure
from becuz.engines.hmem import HMEM
from becuz.engines.world_model import WorldModel
from becuz.orchestration.state import InvestigationState, period
from becuz.schemas import MIN_EFFECT_NGN, TOLERANCE_NGN
from becuz.tracing import Trace

MAX_RETRIES = 2


def verdict(claim: dict, rerun_effect: float | None, rerun_rows: list[str]) -> tuple[str, str]:
    same = (claim["effect_ngn"] is None and rerun_effect is None) or (
        claim["effect_ngn"] is not None and rerun_effect is not None
        and abs(claim["effect_ngn"] - rerun_effect) <= TOLERANCE_NGN)
    if not same or rerun_rows != claim["row_ids"]:
        if claim["retries"] < MAX_RETRIES:
            return "sent_back", "The re-check gave a different result, so it is being tested again."
        return "rejected", "The re-check never matched, so this cause is not reported."
    if rerun_effect is None:
        return "not_tested", "The records for this week cannot measure this cause."
    if rerun_effect >= 0:
        return "rejected", "The records show no loss from this cause this week."
    if rerun_effect > -MIN_EFFECT_NGN:
        return "rejected", f"Too small to matter: {abs(rerun_effect):,.0f} naira."
    if not rerun_rows:
        return "rejected", "No records back this cause."
    return "supported", f"The re-check matched: {abs(rerun_effect):,.0f} naira from {len(rerun_rows)} records."


def make_checker(wh: Warehouse, trace: Trace, world: WorldModel, memory: HMEM):
    def checker(state: InvestigationState) -> dict:
        cause = state["current"]
        claim_id = world.claim_id(cause, period(state))
        claim = world.claims_by_cause(period(state))[cause]
        rerun = measure(wh, cause, state["week_start"], state["week_end"])
        status, reason = verdict(claim, rerun.effect_ngn, rerun.row_ids)
        retries = claim["retries"] + (status == "sent_back")
        world.update_claim(claim_id, "Checker", retries=retries, reason=reason,
                           check={"match": status != "sent_back", "rerun_value_ngn": rerun.effect_ngn, "note": reason})
        world.set_status(claim_id, status, "Checker", reason)
        memory_id = state.get("recalled", {}).get(cause)
        if memory_id and status in ("supported", "rejected"):
            # H-MEM feedback: a remembered cause that holds again gains confidence; one that fails is flagged.
            memory.feedback(memory_id, "helpful" if status == "supported" else "wrong")
        target = "Investigator" if status == "sent_back" or state["queue"] else "Writer"
        trace.emit("Checker", status, cause, reason, target_agent=target, confidence=1.0 if status == "supported" else None,
                   retry_count=retries, status="needs_revision" if status == "sent_back" else "success",
                   engine="world_model")
        return {}

    return checker


def make_router(world: WorldModel):
    def route_after_check(state: InvestigationState) -> Literal["investigator", "writer"]:
        if world.status(world.claim_id(state["current"], period(state))) == "sent_back":
            return "investigator"
        return "investigator" if state["queue"] else "writer"

    return route_after_check
