"""Meterless Scout Intent: a signed execution contract for each investigation.

Python implementation of the contract half of the Scout Intent spec
(github.com/Meterless/Meterless, engines/scout-intent: AGENTS.md, docs/execution-contract.md).
Scout reads the owner's question, picks an intent from a small registry, and issues an
HMAC-signed contract that fixes what the run may touch. Every query then passes through
ContractGate, which refuses unsigned, tampered or out-of-scope work and re-issues an
expired contract (with parentId) instead of extending it.

Choices the spec leaves open, named here:
- Canonical JSON for signing is json.dumps(sort_keys=True, separators=(",", ":")).
- scope.budget.queriesMax is a Becuz extension, set at issue time (never added downstream).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from becuz import ledger

REGISTRY_VERSION = "becuz-intents-1"
POLICY_PACK_VERSION = "becuz-policy-1"
TTL = timedelta(minutes=5)  # spec default; never extended, re-issued instead
QUERIES_MAX = 80  # planner + 6 causes x (investigate + check) x up to 3 attempts, with room to spare

# The intent registry: every intent carries examples (spec: "every intent needs examples").
INTENTS = {
    "profit.explain_change": {
        "examples": ["Why is my profit down this week?", "What made my profit drop?",
                     "Why did I make less money this week?", "Explain my profit change",
                     "How is my shop doing?", "What happened to my business this week?",
                     "Where did my money go?", "Why are my sales down?", "Why is my cash low?"],
        # A question is in scope only if it names the shop's business; helper words only add confidence.
        "domain": ("profit", "profits", "money", "loss", "losses", "lost", "margin", "earn", "earned", "earnings",
                   "income", "revenue", "sales", "sale", "sell", "sold", "selling", "cash", "costs", "cost",
                   "expense", "expenses", "spend", "spent", "stock", "wastage", "waste", "supplier", "suppliers",
                   "price", "prices", "bank", "transfer", "transfers", "till", "pos", "promo", "discount",
                   "customers", "shop", "store", "business"),
        "keywords": ("why", "how", "what", "where", "happened", "doing", "going", "week", "weekly", "down",
                     "drop", "dropped", "fell", "falling", "less", "low", "lower", "worse", "change", "changed",
                     "go", "went", "missing"),
    },
}
# The only tables an investigation may read; anything else is refused.
CAPABILITIES = ("daily_pnl", "sales", "sale_lines", "products", "promos", "stock_movements",
                "bank_statement", "supplier_invoices", "expenses", "transfer_check")


class ContractRefused(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(contract: dict) -> bytes:
    unsigned = {k: v for k, v in contract.items() if k != "signature"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _contract_id() -> str:
    # ULID-like: millisecond time prefix keeps ids monotonic, random suffix keeps them unique.
    return f"{int(time.time() * 1000):013x}{secrets.token_hex(6)}"


class Scout:
    def __init__(self, key: bytes | None = None, log_path: Path | None = None, clock=_now):
        # A per-process key is enough: contracts live only for one run. SCOUT_SIGNING_KEY pins it.
        self.key = key or os.getenv("SCOUT_SIGNING_KEY", "").encode() or secrets.token_bytes(32)
        self.log_path, self.clock = log_path, clock

    def log(self, event: str, contract: dict | None, **detail) -> None:
        ledger.write(self.log_path, {"kind": event, "engine": "scout_intent",
                                     "contractId": contract and contract.get("contractId"),
                                     "traceId": contract and contract.get("traceId"), **detail})

    def classify(self, question: str) -> tuple[str, float]:
        words = set(re.findall(r"[a-z]+", question.lower()))
        # No word about the shop's business means out of scope (confidence 0), whatever else it says.
        scores = {name: (len(words & set(spec["domain"])) + len(words & set(spec["keywords"]))) / 3
                  if words & set(spec["domain"]) else 0.0 for name, spec in INTENTS.items()}
        best = max(scores, key=scores.get)
        return best, min(1.0, scores[best])

    def sign(self, contract: dict) -> dict:
        signed = dict(contract)
        signed["signature"] = hmac.new(self.key, _canonical(contract), hashlib.sha256).hexdigest()
        return signed

    def decide(self, question: str, trace_id: str, parent_id: str | None = None) -> dict:
        intent, confidence = self.classify(question)
        issued = self.clock()
        contract = {
            "contractId": _contract_id(), "parentId": parent_id, "traceId": trace_id,
            "intent": {"primary": intent, "parameters": {"metric": "profit", "period": "one week"},
                       "references": [], "confidence": confidence, "alternates": []},
            "risk": {"level": "low", "flags": ["read_only"], "redactions": [], "approvals": []},
            "toolPlan": ["sql.read"], "modelProfile": "becuz",
            "scope": {"user": "owner", "surface": "becuz", "capabilities": list(CAPABILITIES),
                      "budget": {"tokensMax": 0, "costMaxUSD": 0, "queriesMax": QUERIES_MAX}},
            "issuedAt": issued.isoformat(), "expiresAt": (issued + TTL).isoformat(),
            "registryVersion": REGISTRY_VERSION, "policyPackVersion": POLICY_PACK_VERSION, "signedBy": "scout",
        }
        signed = self.sign(contract)
        self.log("contract.issued", signed, intent=intent, confidence=confidence)
        return signed

    def replan(self, parent: dict, reason: str) -> dict:
        self.log("scout.replan", parent, reason=reason)
        return self.decide("Explain my profit change", parent["traceId"], parent_id=parent["contractId"])

    def verify(self, contract: dict) -> None:
        signature = contract.get("signature")
        if not signature:
            self.log("contract.refused", contract, reason="unsigned")
            raise ContractRefused("unsigned")
        expected = hmac.new(self.key, _canonical(contract), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            self.log("contract.refused", contract, reason="tampered")
            raise ContractRefused("tampered")
        if self.clock() >= datetime.fromisoformat(contract["expiresAt"]):
            self.log("contract.expired", contract)
            raise ContractRefused("expired")


class ContractGate:
    """Wraps a warehouse: every query must fit the current signed contract."""

    def __init__(self, wh, scout: Scout):
        self.wh, self.scout, self.via, self.usl = wh, scout, wh.via, wh.usl
        self.contract: dict | None = None
        self.used = 0
        self.table = re.compile(re.escape(wh.usl) + r"\.(\w+)")

    def open(self, question: str, trace_id: str) -> dict:
        self.contract = self.scout.decide(question, trace_id)
        return self.contract

    def query(self, sql: str) -> list[dict]:
        if self.contract is None:
            raise ContractRefused("no contract")
        try:
            self.scout.verify(self.contract)
        except ContractRefused as exc:
            if exc.reason != "expired":
                raise
            self.contract = self.scout.replan(self.contract, "expired during the run")
        scope = self.contract["scope"]
        outside = sorted(set(self.table.findall(sql)) - set(scope["capabilities"]))
        if outside:
            self.scout.log("contract.refused", self.contract, reason="scope-mismatch", tables=outside)
            raise ContractRefused(f"scope-mismatch: {', '.join(outside)}")
        if self.used >= scope["budget"]["queriesMax"]:
            self.scout.log("contract.refused", self.contract, reason="budget-exhausted")
            raise ContractRefused("budget-exhausted")
        self.used += 1
        self.scout.log("contract.verified", self.contract, queries_used=self.used)
        return self.wh.query(sql)

