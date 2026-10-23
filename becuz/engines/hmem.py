"""Meterless H-MEM: memory of causes the owner has confirmed, recalled before each investigation.

Python implementation of the H-MEM spec (github.com/Meterless/Meterless, engines/hmem;
the doc's §4, §8, §11, §13): a store of records with provenance, a retrieval service
that ranks them, feedback that moves confidence by the spec's fixed amounts, and a
trust ledger appended to logs/hmem.jsonl. Only owner-confirmed facts are written,
between runs (an out-of-band approval, not a prompt during a run).

Ranking needs no embeddings: token overlap x layer weight x confidence, with a
penalty for superseded records (the spec's conformance ranking is embedding-independent).
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from becuz import ledger

FEEDBACK = {"helpful": (0.05, 1), "not_helpful": (-0.03, 0), "wrong": (-0.20, 0)}  # spec-fixed deltas
LAYER_WEIGHT = {"long_term": 1.0, "working": 0.8, "short_term": 0.6}
SUPERSEDED_PENALTY = 0.1
TOP_N = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


class HMEM:
    def __init__(self, path: Path | None = None, ledger_path: Path | None = None, clock=_now):
        self.path, self.ledger_path, self.clock = path, ledger_path, clock
        self.records: list[dict] = json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else []
        self.ledger: list[dict] = []

    def _save(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def _audit(self, memory_id: str, action: str, actor: str, previous: dict | None, new: dict | None) -> None:
        entry = {"memoryId": memory_id, "action": action, "actor": actor, "timestamp": self.clock(),
                 "previousState": previous, "newState": new}
        self.ledger.append(entry)
        ledger.write(self.ledger_path, {"kind": f"hmem.{action}", "engine": "hmem", **entry})

    def get(self, memory_id: str) -> dict:
        return next(r for r in self.records if r["id"] == memory_id)

    def add(self, content: str, source: str, *, type: str = "factual", layer: str = "long_term",
            tags: list[str] = (), confidence: float = 0.7, agent_id: str = "", run_id: str = "",
            related_to: list[str] = ()) -> str:
        if not source:
            raise ValueError("every memory needs a source (provenance)")
        record = {"id": f"mem-{uuid.uuid4().hex[:12]}", "content": content, "type": type, "layer": layer,
                  "timestamp": self.clock(), "lastAccessed": None, "accessCount": 0, "tags": list(tags),
                  "confidence": confidence, "source": source, "agentId": agent_id, "runId": run_id,
                  "relatedTo": list(related_to), "supersededBy": None}
        self.records.append(record)
        self._audit(record["id"], "create", agent_id or source, None, {"confidence": confidence})
        self._save()
        return record["id"]

    def feedback(self, memory_id: str, kind: str, actor: str = "Checker") -> dict:
        delta, access = FEEDBACK[kind]
        record = self.get(memory_id)
        before = {"confidence": record["confidence"], "tags": list(record["tags"])}
        record["confidence"] = round(min(1.0, max(0.0, record["confidence"] + delta)), 4)
        record["accessCount"] += access
        record["lastAccessed"] = self.clock()
        if kind == "wrong" and "review" not in record["tags"]:
            record["tags"].append("review")
        self._audit(memory_id, f"feedback.{kind}", actor, before,
                    {"confidence": record["confidence"], "tags": list(record["tags"])})
        self._save()
        return record

    def supersede(self, old_id: str, new_id: str, actor: str = "owner") -> None:
        self.get(old_id)["supersededBy"] = new_id
        self._audit(old_id, "supersede", actor, None, {"supersededBy": new_id})
        self._save()

    def query(self, text: str, tags: list[str] = (), limit: int = TOP_N) -> dict:
        """Ranked recall, returned as a structured payload with the reason for each hit (spec §8)."""
        words = _tokens(text)
        hits = []
        for record in self.records:
            if tags and not set(tags) <= set(record["tags"]):
                continue
            overlap = len(words & _tokens(record["content"])) or (1 if tags else 0)
            if not overlap:
                continue
            score = overlap * LAYER_WEIGHT[record["layer"]] * record["confidence"]
            if record["supersededBy"]:
                score *= SUPERSEDED_PENALTY
            hits.append({"memory": record, "score": round(score, 4),
                         "retrievalReason": f"{overlap} shared terms, {record['layer']}, confidence {record['confidence']}"})
        hits.sort(key=lambda h: h["score"], reverse=True)
        return {"strategy": "task_focused", "results": hits[:limit]}
