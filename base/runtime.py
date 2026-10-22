from __future__ import annotations

from .agent import Agent
from .config import Config, load
from .memory import JsonMemory, Memory, NullMemory
from .pipeline import Pipeline
from .policy import load_policy
from .registry import build_registry


def build_memory(config: Config) -> Memory:
    path = str(config.memory_path).strip()
    if not path or path.lower() == "none":
        return NullMemory()
    return JsonMemory(config.memory_path)


def build_agent(config: Config | None = None) -> Agent:
    config = config or load()
    pipeline = Pipeline(config)
    memory = build_memory(config)
    registry = build_registry(pipeline, memory)
    policy = load_policy(config)
    for tool in getattr(policy, "tools", lambda: [])():
        registry.register(tool)
    return Agent(config, registry, policy, memory)
