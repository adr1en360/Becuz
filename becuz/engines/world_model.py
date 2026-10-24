"""Meterless World Model: the shared claims list every Becuz agent reads.

Python implementation of the World Model spec (github.com/Meterless/Meterless,
engines/world-model; the doc's §3-§4, §10, §11) as a pure graph: nodes with
content-hash IDs and provenance, and edges with validFrom/validTo so history is
never overwritten. Claims are nodes; their status is a bitemporal edge, so the
Checker's verdict closes "proposed" instead of erasing it. Every mutation is
audited with a strictly increasing seq and appended to logs/world.jsonl.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from becuz import ledger

AUTO_MERGE, REVIEW = 0.85, 0.82  # similarity bands from the spec's decide()


def normalize_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", plain.replace(" ", " ")).strip().lower()


def entity_id(kind: str, name: str) -> str:
    return "ent_" + hashlib.sha256(f"{kind}:{normalize_name(name)}".encode()).hexdigest()[:16]


def decide(similarity: float) -> str:
    if similarity >= AUTO_MERGE:
        return "auto-merge"
    return "review" if similarity >= REVIEW else "new"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorldModel:
    def __init__(self, log_path: Path | None = None, clock=_now):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self.audit: list[dict] = []
        self.log_path, self.clock = log_path, clock

    def _record(self, action: str, node_id: str, agent: str, **detail) -> None:
        entry = {"seq": len(self.audit) + 1, "action": action, "id": node_id, "agentId": agent, "at": self.clock(), **detail}
        self.audit.append(entry)
        ledger.write(self.log_path, {"kind": f"world.{action}", "engine": "world_model", **entry})

    def upsert_entity(self, kind: str, name: str, source: dict, agent: str, run_id: str = "", **properties) -> str:
        if not source:
            raise ValueError("every write needs a source (provenance)")
        node_id = entity_id(kind, name)
        before = self.nodes.get(node_id)
        node = {"id": node_id, "type": kind, "name": normalize_name(name),
                "properties": {**(before or {}).get("properties", {}), **properties},
                "provenance": [*(before or {}).get("provenance", []), source], "agentId": agent, "runId": run_id}
        if before and before["properties"] == node["properties"] and source in before["provenance"]:
            return node_id  # nothing new: idempotent
        self.nodes[node_id] = node
        self._record("upsert", node_id, agent)
        return node_id

    def ingest(self, batch: list[dict], agent: str) -> bool:
        """Idempotent: re-ingesting the same batch changes nothing."""
        before = self.canonical_shape()
        for item in batch:
            self.upsert_entity(item["type"], item["name"], item["source"], agent, **item.get("properties", {}))
        return self.canonical_shape() != before

    def canonical_shape(self) -> str:
        nodes = {k: {**v, "agentId": None, "runId": None} for k, v in sorted(self.nodes.items())}
        return json.dumps({"nodes": nodes, "edges": self.edges}, sort_keys=True, default=str)

    # Claims: the shared list the four agents use.

    @staticmethod
    def claim_id(cause_id: str, period: str) -> str:
        return entity_id("claim", f"{cause_id}@{period}")

    def propose_claim(self, cause_id: str, period: str, agent: str, run_id: str, **evidence) -> str:
        claim_id = self.upsert_entity("claim", f"{cause_id}@{period}", {"kind": "agent", "agent": agent},
                                      agent, run_id, cause_id=cause_id, period=period, **evidence)
        self.set_status(claim_id, "proposed", agent)
        return claim_id

    def update_claim(self, claim_id: str, agent: str, **properties) -> None:
        self.nodes[claim_id]["properties"].update(properties)
        self._record("update", claim_id, agent, fields=sorted(properties))

    def set_status(self, claim_id: str, status: str, agent: str, reason: str = "") -> None:
        now = self.clock()
        for edge in self.edges:
            if edge["from"] == claim_id and edge["type"] == "status" and edge["validTo"] is None:
                edge["validTo"] = now  # supersede, never erase
        self.edges.append({"from": claim_id, "to": status, "type": "status", "agentId": agent,
                           "properties": {"reason": reason}, "validFrom": now, "validTo": None})
        self._record("status", claim_id, agent, status=status, reason=reason)

    def status(self, claim_id: str, at: str | None = None) -> str | None:
        for edge in reversed(self.edges):
            if edge["from"] != claim_id or edge["type"] != "status":
                continue
            if at is None and edge["validTo"] is None:
                return edge["to"]
            if at is not None and edge["validFrom"] <= at and (edge["validTo"] is None or at < edge["validTo"]):
                return edge["to"]
        return None

    def history(self, claim_id: str) -> list[str]:
        return [e["to"] for e in self.edges if e["from"] == claim_id and e["type"] == "status"]

    def claims(self, status: str | None = None) -> list[dict]:
        found = [{**n["properties"], "claim_id": k, "status": self.status(k)}
                 for k, n in self.nodes.items() if n["type"] == "claim"]
        return [c for c in found if status is None or c["status"] == status]

    def claims_by_cause(self, period: str) -> dict[str, dict]:
        return {c["cause_id"]: c for c in self.claims() if c.get("period") == period}

    def context_for(self, role: str) -> dict:
        """Structured context for an agent, with the reason it was selected (spec §10)."""
        if role == "writer":
            return {"selectionReason": "only claims the Checker supported may reach the report",
                    "claims": self.claims("supported")}
        return {"selectionReason": "all claims and their current status", "claims": self.claims()}
