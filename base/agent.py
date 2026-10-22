from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from . import ledger
from .memory import Memory
from .providers import redact


@dataclass
class Action:
    tool: str
    args: dict = field(default_factory=dict)


@dataclass
class Observation:
    tool: str
    ok: bool
    result: Any = None
    error: str = ""


@dataclass
class RunState:
    request: str
    memory: Memory
    observations: list[Observation] = field(default_factory=list)
    scratch: dict = field(default_factory=dict)
    trace: list[dict] = field(default_factory=list)


class Policy:
    """One idea plugs in here. Keep state in RunState, not on the policy."""

    def next(self, state: RunState) -> Action | None:
        raise NotImplementedError

    def observe(self, state: RunState, observation: Observation) -> None:
        return None

    def result(self, state: RunState) -> dict:
        if not state.observations:
            return {"ok": False, "error": "no action"}
        observation = state.observations[-1]
        if isinstance(observation.result, dict):
            return observation.result
        return {
            "ok": observation.ok,
            "result": observation.result,
            "error": observation.error,
        }

    def tools(self) -> list["Tool"]:
        return []


@dataclass
class Tool:
    name: str
    description: str
    run: Callable[[dict, RunState], Any]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def run(self, action: Action, state: RunState) -> Observation:
        tool = self._tools.get(action.tool)
        if tool is None:
            return Observation(action.tool, False, error=f"unknown tool: {action.tool}")
        if not isinstance(action.args, dict):
            return Observation(action.tool, False, error="tool args must be an object")
        try:
            return Observation(action.tool, True, result=tool.run(action.args, state))
        except Exception as exc:
            return Observation(action.tool, False, error=redact(str(exc)))


class Agent:
    def __init__(self, config, registry: ToolRegistry, policy: Policy, memory: Memory):
        self.config = config
        self.registry = registry
        self.policy = policy
        self.memory = memory

    def run(self, request: str) -> dict:
        request = (request or "").strip()
        if not request:
            return {"ok": False, "error": "empty request", "trace": [], "steps": 0}
        run_id = uuid.uuid4().hex[:12]
        state = RunState(request=request, memory=self.memory)
        max_steps = max(1, int(getattr(self.config, "max_steps", 6)))

        for step in range(1, max_steps + 1):
            try:
                action = self.policy.next(state)
            except Exception as exc:
                error = redact(str(exc))
                state.trace.append(
                    {
                        "run_id": run_id,
                        "step": step,
                        "tool": "policy",
                        "args": {},
                        "ok": False,
                        "error": error,
                        "duration_ms": 0.0,
                    }
                )
                return {
                    "ok": False,
                    "error": f"policy failed: {error}",
                    "run_id": run_id,
                    "trace": state.trace,
                    "steps": len(state.trace),
                }
            if action is None:
                break

            started = time.perf_counter()
            observation = self.registry.run(action, state)
            elapsed = round((time.perf_counter() - started) * 1000, 1)
            state.observations.append(observation)
            entry = {
                "run_id": run_id,
                "step": step,
                "tool": action.tool,
                "args": _safe_args(action.args),
                "ok": observation.ok,
                "error": observation.error,
                "duration_ms": elapsed,
            }
            state.trace.append(entry)
            self._record(entry)
            try:
                self.policy.observe(state, observation)
            except Exception as exc:
                message = redact(str(exc))
                error = {
                    "run_id": run_id,
                    "step": step,
                    "tool": "policy.observe",
                    "args": {},
                    "ok": False,
                    "error": message,
                    "duration_ms": 0.0,
                }
                state.trace.append(error)
                self._record(error)
                return {
                    "ok": False,
                    "error": f"policy observe failed: {message}",
                    "run_id": run_id,
                    "trace": state.trace,
                    "steps": len(state.trace),
                }

        try:
            result = self.policy.result(state)
        except Exception as exc:
            result = {"ok": False, "error": f"policy result failed: {redact(str(exc))}"}
        if not isinstance(result, dict):
            result = {"ok": False, "error": "policy result is not a dict"}

        result.setdefault(
            "ok", bool(state.observations) and all(item.ok for item in state.observations)
        )
        result["run_id"] = run_id
        result["trace"] = state.trace
        result["steps"] = len(state.trace)
        return result

    def _record(self, entry: dict) -> None:
        path = getattr(self.config, "trace_path", None)
        if path:
            ledger.write(Path(path), {"kind": "agent_step", **entry})


def _safe_args(value: Any, depth: int = 0) -> Any:
    if depth >= 3:
        return "..."
    if isinstance(value, dict):
        return {
            redact(str(key))[:40]: _safe_args(item, depth + 1)
            for key, item in list(value.items())[:20]
        }
    if isinstance(value, (list, tuple)):
        return [_safe_args(item, depth + 1) for item in value[:20]]
    if isinstance(value, str):
        text = redact(value)
        return text[:200] + ("..." if len(text) > 200 else "")
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return redact(str(value)[:200])
