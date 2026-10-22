from __future__ import annotations

from .agent import Tool, ToolRegistry
from .memory import Memory
from .pipeline import Pipeline


def build_registry(pipeline: Pipeline, memory: Memory) -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        Tool(
            "query_data",
            "Run one read-only SQL query on Zetaris.",
            lambda args, state: pipeline.query(str(args.get("sql", ""))),
        )
    )
    registry.register(
        Tool(
            "ask_model",
            "Ask the configured model a question.",
            lambda args, state: pipeline.answer(
                str(args.get("prompt", "")),
                system=str(args.get("system", "")),
            ),
        )
    )
    registry.register(
        Tool(
            "remember",
            "Store one text memory.",
            lambda args, state: _remember(memory, args),
        )
    )
    registry.register(
        Tool(
            "recall",
            "Retrieve memories related to a query.",
            lambda args, state: _recall(memory, args),
        )
    )
    registry.register(
        Tool(
            "blocked",
            "Return a blocked result without calling a provider.",
            lambda args, state: pipeline.blocked(
                str(args.get("request", "")),
                str(args.get("reason", "blocked")),
            ),
        )
    )
    return registry


def _remember(memory: Memory, args: dict) -> dict:
    text = str(args.get("text", "")).strip()
    metadata = args.get("metadata") or {}
    namespace = str(args.get("namespace", "default"))
    memory.remember(text, metadata, namespace)
    return {"ok": True, "remembered": bool(text), "text": text[:200]}


def _recall(memory: Memory, args: dict) -> dict:
    items = memory.recall(
        str(args.get("query", "")),
        limit=max(1, int(args.get("limit", 5))),
        namespace=str(args.get("namespace", "default")),
    )
    return {
        "ok": True,
        "items": [
            {"text": item.text, "metadata": item.metadata, "ts": item.ts}
            for item in items
        ],
    }
