"""Investigator: tests one cause with its catalogue SQL and writes a claim to the shared list."""
from __future__ import annotations

from becuz.adapters import Warehouse
from becuz.catalogue import measure
from becuz.orchestration.state import Claim, InvestigationState
from becuz.tracing import Trace


def make_investigator(wh: Warehouse, trace: Trace):
    def investigator(state: InvestigationState) -> dict:
        claims, queue = dict(state["claims"]), list(state["queue"])
        current = state.get("current")
        if current and claims[current]["status"] == "sent_back":
            cause, retries = current, claims[current]["retries"]  # the Checker sent this one back
        else:
            cause, retries = queue.pop(0), 0
        m = measure(wh, cause, state["week_start"], state["week_end"])
        claims[cause] = Claim(cause_id=cause, status="open", effect_ngn=m.effect_ngn, row_ids=m.row_ids,
                              effect_sql=m.effect_sql, records_sql=m.records_sql, retries=retries, check=None, reason="")
        effect = "not measurable" if m.effect_ngn is None else f"{m.effect_ngn:+,.0f}"
        trace.emit("Investigator", "test_cause", cause, f"effect {effect} from {len(m.row_ids)} records",
                   target_agent="Checker", retry_count=retries, via=wh.via)
        return {"claims": claims, "queue": queue, "current": cause}

    return investigator
