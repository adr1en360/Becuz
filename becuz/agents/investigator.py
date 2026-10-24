"""Investigator: tests one cause with its catalogue SQL and writes the claim to the World Model."""
from __future__ import annotations

from becuz.adapters import Warehouse
from becuz.catalogue import measure
from becuz.engines.world_model import WorldModel
from becuz.orchestration.state import InvestigationState, period
from becuz.tracing import Trace


def make_investigator(wh: Warehouse, trace: Trace, world: WorldModel):
    def investigator(state: InvestigationState) -> dict:
        queue, current = list(state["queue"]), state.get("current")
        sent_back = current and world.status(world.claim_id(current, period(state))) == "sent_back"
        cause = current if sent_back else queue.pop(0)
        retries = world.claims_by_cause(period(state)).get(cause, {}).get("retries", 0)
        m = measure(wh, cause, state["week_start"], state["week_end"])
        world.propose_claim(cause, period(state), "Investigator", trace.run_id, effect_ngn=m.effect_ngn,
                            row_ids=m.row_ids, effect_sql=m.effect_sql, records_sql=m.records_sql, retries=retries)
        effect = "not measurable" if m.effect_ngn is None else f"{m.effect_ngn:+,.0f}"
        trace.emit("Investigator", "test_cause", cause, f"effect {effect} from {len(m.row_ids)} records",
                   target_agent="Checker", retry_count=retries, via=wh.via, engine="world_model")
        return {"queue": queue, "current": cause}

    return investigator
