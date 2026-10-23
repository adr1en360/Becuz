"""Per-run trace: one JSONL line per agent decision in logs/trace-<run_id>.jsonl, echoed to stdout.

Every line carries the fields the hackathon asks for: timestamp, run_id, agent_name,
action, input_summary, output_summary, target_agent, confidence, retry_count, status.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from becuz.safety import redact


class Trace:
    def __init__(self, run_id: str, folder: Path | None):
        self.run_id = run_id
        self.path = folder / f"trace-{run_id}.jsonl" if folder else None
        self.lines = 0

    def emit(self, agent_name: str, action: str, input_summary: str, output_summary: str,
             target_agent: str | None = None, confidence: float | None = None, retry_count: int = 0,
             status: str = "success", **extra) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": self.run_id, "agent_name": agent_name, "action": action,
            "input_summary": input_summary, "output_summary": output_summary, "target_agent": target_agent,
            "confidence": confidence, "retry_count": retry_count, "status": status, **extra,
        }
        line = redact(json.dumps(event, ensure_ascii=True, default=str))
        self.lines += 1
        print(f"[{status}] run_id={self.run_id} {agent_name} {action}: {output_summary}", file=sys.stderr)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
