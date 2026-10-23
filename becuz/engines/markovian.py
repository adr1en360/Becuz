"""Meterless Markovian: the Checker's reviews run as a chain of bounded chunks with compressed carryover.

Python implementation of the Markovian spec (github.com/Meterless/Meterless, engines/markovian;
the doc's §3-§7 and docs/efficiency-model.md). Each Checker review is one chunk: the model sees
the fixed framing, this claim, and a short carryover of earlier verdicts instead of the whole
history, so each call stays the same size. The engine strips the spec's markers, builds the
carryover by the spec's cascade (explicit override, heuristic extraction, tail truncation; the
LLM-compression tier is not used), and logs each run's token savings, labelled "estimated".

Adaptation, named: the spec targets one long generative chain; here the chain is the Checker loop.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass, field

from becuz import ledger

CHECKPOINT, COMPLETE = "[STATE_CHECKPOINT]", "[TASK_COMPLETE]"


class ConfigError(ValueError):
    """Out-of-range config is rejected, never clamped (conformance cfg-001)."""


@dataclass(frozen=True)
class ChunkConfig:
    chunk_size: int = 8000
    max_chunks: int = 12
    carryover_tokens: int = 256
    overlap_tokens: int = 0  # reserved by the spec; any non-zero value is rejected (ovl-001)

    def __post_init__(self):
        if not (1000 <= self.chunk_size <= 128000 and self.chunk_size % 1000 == 0):
            raise ConfigError(f"chunk_size {self.chunk_size} must be 1000..128000 in steps of 1000")
        if not (128 <= self.carryover_tokens <= 32768 and self.carryover_tokens % 128 == 0):
            raise ConfigError(f"carryover_tokens {self.carryover_tokens} must be 128..32768 in steps of 128")
        if self.max_chunks < 1:
            raise ConfigError("max_chunks must be at least 1")
        if self.overlap_tokens != 0:
            raise ConfigError("overlap_tokens is reserved and must be 0")


def tokens(text: str) -> int:
    return math.ceil(len(text) / 4)  # the spec's estimate


def model_totals(n: int, framing: int = 400, goal: int = 200, step: int = 300, output: int = 1200,
                 carryover: int = 800) -> dict:
    """Modelled cost of n steps: append-history vs Markovian (efficiency-model.md)."""
    naive = n * (framing + goal + step) + output * n * (n - 1) // 2
    markovian = n * (framing + goal + carryover + step)
    return {"naive": naive, "markovian": markovian, "efficiency": (naive - markovian) / naive}


def run_efficiency(chunk_tokens: list[int], config: ChunkConfig) -> dict:
    """Cost of an actual chain: resending all earlier chunks vs carrying a fixed carryover."""
    standard = sum(sum(chunk_tokens[:i]) + t for i, t in enumerate(chunk_tokens))
    markovian = len(chunk_tokens) * config.carryover_tokens + sum(chunk_tokens)
    return {"standardCost": standard, "markovianCost": markovian, "saved": standard - markovian,
            "efficiencyPercent": round((standard - markovian) / standard * 100, 2) if standard else 0.0}


def strip_markers(text: str) -> tuple[str, str | None, bool]:
    """Returns (clean text, explicit carryover after STATE_CHECKPOINT if any, task complete?)."""
    complete = COMPLETE in text
    text = text.replace(COMPLETE, "")
    explicit = None
    if CHECKPOINT in text:
        text, _, explicit = text.partition(CHECKPOINT)
        explicit = explicit.strip() or None
    return text.strip(), explicit, complete


@dataclass
class MarkovianRun:
    run_id: str
    agent_id: str
    mode: str
    chunk_config: dict
    chunks: list[dict] = field(default_factory=list)
    started: float = field(default_factory=time.monotonic)
    completed: bool = False


class Markovian:
    def __init__(self, run_id: str, agent_id: str = "Checker", mode: str = "CHECKER",
                 config: ChunkConfig | None = None, log_path=None, reflect=None):
        self.config = config or ChunkConfig()
        self.run = MarkovianRun(run_id, agent_id, mode, asdict(self.config))  # snapshot (snap-001)
        self.carryover = ""
        self.log_path, self.reflect = log_path, reflect

    def compress(self, explicit: str | None, latest: str) -> str:
        # Spec cascade: explicit override, then heuristic extraction, then tail truncation.
        candidate = explicit or "\n".join(filter(None, [self.carryover, latest.splitlines()[0] if latest else ""]))
        limit = self.config.carryover_tokens * 4
        return candidate[-limit:]

    def step(self, build_messages, generate) -> str:
        """One chunk: build messages from the carryover, generate, strip markers, update the carryover."""
        if len(self.run.chunks) >= self.config.max_chunks:
            raise ConfigError("max_chunks reached")
        messages = build_messages(self.carryover)
        raw = generate(messages)
        clean, explicit, complete = strip_markers(raw)
        sent = sum(tokens(m["content"]) for m in messages)
        self.run.chunks.append({"id": len(self.run.chunks) + 1, "tokens": sent + tokens(clean),
                                "carryover": self.carryover, "content": clean})
        self.carryover = self.compress(explicit, clean)
        self.run.completed = self.run.completed or complete
        return clean

    def finish(self) -> dict:
        report = run_efficiency([c["tokens"] for c in self.run.chunks], self.config)
        record = {"kind": "markovian.run", "engine": "markovian", "runId": self.run.run_id,
                  "agentId": self.run.agent_id, "mode": self.run.mode, "chunkConfig": self.run.chunk_config,
                  "chunks": len(self.run.chunks), "totalTokensUsed": sum(c["tokens"] for c in self.run.chunks),
                  "totalTokensSaved": report["saved"], "efficiencyPercent": report["efficiencyPercent"],
                  "tokenLabel": "estimated", "durationMs": round((time.monotonic() - self.run.started) * 1000),
                  "status": "completed"}
        if self.reflect:
            try:
                record["reflection"] = self.reflect(record)
            except Exception as exc:  # a failed reflection must not fail the run (ref-001)
                record["reflection_error"] = type(exc).__name__
        self.run.completed = True
        ledger.write(self.log_path, record)
        return record
