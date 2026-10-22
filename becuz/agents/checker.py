"""Checker: re-runs each claim's SQL itself and supports, rejects or sends it back.

No claim reaches the report unless the re-run matches, the effect is a real loss
of at least MIN_EFFECT_NGN, and record IDs back it.
"""
from __future__ import annotations

from typing import Literal

from becuz.adapters import Warehouse
from becuz.catalogue import measure
from becuz.orchestration.state import InvestigationState
from becuz.schemas import MIN_EFFECT_NGN, TOLERANCE_NGN
from becuz.tracing import Trace

MAX_RETRIES = 2


def verdict(claim: dict, rerun_effect: float | None, rerun_rows: list[str]) -> tuple[str, str]:
    same = (claim["effect_ngn"] is None and rerun_effect is None) or (
        claim["effect_ngn"] is not None and rerun_effect is not None
        and abs(claim["effect_ngn"] - rerun_effect) <= TOLERANCE_NGN)
    if not same or rerun_rows != claim["row_ids"]:
        if claim["retries"] < MAX_RETRIES:
            return "sent_back", "the re-run gave a different result"
        return "rejected", "the re-run never matched"
    if rerun_effect is None:
        return "not_tested", "the data cannot measure this cause for the week"
    if rerun_effect >= 0:
        return "rejected", f"no loss: measured {rerun_effect:+,.0f}"
    if rerun_effect > -MIN_EFFECT_NGN:
        return "rejected", f"too small to matter: {rerun_effect:+,.0f}"
    if not rerun_rows:
        return "rejected", "no records back it"
    return "supported", f"re-run matched {rerun_effect:+,.0f} with {len(rerun_rows)} records"


def make_checker(wh: Warehouse, trace: Trace):
    def checker(state: InvestigationState) -> dict:
        cause = state["current"]
        claims = dict(state["claims"])
        claim = dict(claims[cause])
        rerun = measure(wh, cause, state["week_start"], state["week_end"])
        status, reason = verdict(claim, rerun.effect_ngn, rerun.row_ids)
        claim.update(status=status, reason=reason,
                     retries=claim["retries"] + (status == "sent_back"),
                     check={"match": status != "sent_back", "rerun_value_ngn": rerun.effect_ngn, "note": reason})
        claims[cause] = claim
        target = "Investigator" if status == "sent_back" or state["queue"] else "Writer"
        trace.emit("Checker", status, cause, reason, target_agent=target, confidence=1.0 if status == "supported" else None,
                   retry_count=claim["retries"], status="needs_revision" if status == "sent_back" else "success")
        return {"claims": claims}

    return checker


def route_after_check(state: InvestigationState) -> Literal["investigator", "writer"]:
    if state["claims"][state["current"]]["status"] == "sent_back":
        return "investigator"
    return "investigator" if state["queue"] else "writer"
