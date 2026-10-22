from __future__ import annotations

import importlib

from . import scout
from .agent import Action, Policy, RunState


class ScoutPolicy(Policy):
    """Default one-step policy. Replace it when the idea is ready."""

    def next(self, state: RunState) -> Action | None:
        if state.observations:
            return None
        decision = scout.classify(state.request)
        if decision.tool == "blocked":
            return Action(
                "blocked",
                {"request": state.request, "reason": decision.reason},
            )
        if decision.tool == "query_data":
            return Action("query_data", {"sql": decision.sql})
        return Action("ask_model", {"prompt": decision.prompt})


def load_policy(config) -> Policy:
    spec = str(getattr(config, "agent_policy", "") or "").strip()
    if not spec:
        return ScoutPolicy()
    if ":" not in spec:
        raise ValueError("AGENT_POLICY must look like module:Class")
    module_name, class_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    factory = getattr(module, class_name)
    policy = factory()
    if not isinstance(policy, Policy):
        for method in ("next", "result"):
            if not callable(getattr(policy, method, None)):
                raise TypeError(f"{spec} does not implement {method}()")
    return policy
