from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from base.agent import Action, Agent, Policy, Tool, ToolRegistry
from base.memory import NullMemory
from base.policy import ScoutPolicy


class FakePipeline:
    def query(self, sql: str) -> dict:
        return {"ok": True, "tool": "query_data", "sql": sql, "rows": [[1]]}

    def answer(self, prompt: str, system: str = "") -> dict:
        return {"ok": True, "tool": "ask_model", "answer": "answer", "system": system}

    def blocked(self, request: str, reason: str) -> dict:
        return {"ok": False, "blocked": True, "reason": reason}


def build_registry(pipeline: FakePipeline) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        Tool("query_data", "", lambda args, state: pipeline.query(args["sql"]))
    )
    registry.register(
        Tool(
            "ask_model",
            "",
            lambda args, state: pipeline.answer(
                args["prompt"], args.get("system", "")
            ),
        )
    )
    registry.register(
        Tool(
            "blocked",
            "",
            lambda args, state: pipeline.blocked(args["request"], args["reason"]),
        )
    )
    return registry


class AgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.config = SimpleNamespace(
            max_steps=3,
            trace_path=Path(self.tmp.name) / "trace.jsonl",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_sql(self) -> None:
        agent = Agent(
            self.config,
            build_registry(FakePipeline()),
            ScoutPolicy(),
            NullMemory(),
        )
        result = agent.run("SELECT 1 AS one")
        self.assertTrue(result["ok"])
        self.assertEqual(result["tool"], "query_data")
        self.assertEqual(len(result["trace"]), 1)
        self.assertTrue(self.config.trace_path.exists())

    def test_question(self) -> None:
        agent = Agent(
            self.config,
            build_registry(FakePipeline()),
            ScoutPolicy(),
            NullMemory(),
        )
        result = agent.run("Explain revenue.")
        self.assertTrue(result["ok"])
        self.assertEqual(result["tool"], "ask_model")

    def test_blocked(self) -> None:
        agent = Agent(
            self.config,
            build_registry(FakePipeline()),
            ScoutPolicy(),
            NullMemory(),
        )
        result = agent.run("DROP TABLE orders")
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])

    def test_max_steps(self) -> None:
        class LoopPolicy(Policy):
            def next(self, state):
                return Action("echo", {"n": len(state.observations)})

            def result(self, state):
                return {"ok": True, "done": True}

        registry = ToolRegistry()
        registry.register(Tool("echo", "", lambda args, state: {"ok": True, "n": args["n"]}))
        agent = Agent(self.config, registry, LoopPolicy(), NullMemory())
        result = agent.run("loop")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["trace"]), 3)

    def test_custom_tool(self) -> None:
        class OneTool(Policy):
            def next(self, state):
                return None if state.observations else Action("echo", {"x": 1})

            def result(self, state):
                return state.observations[-1].result

        registry = ToolRegistry()
        registry.register(Tool("echo", "", lambda args, state: {"ok": True, "x": args["x"]}))
        agent = Agent(self.config, registry, OneTool(), NullMemory())
        result = agent.run("x")
        self.assertTrue(result["ok"])
        self.assertEqual(result["x"], 1)
        self.assertEqual(result["steps"], 1)

    def test_duplicate_tool(self) -> None:
        registry = ToolRegistry()
        tool = Tool("echo", "", lambda args, state: {"ok": True})
        registry.register(tool)
        with self.assertRaises(ValueError):
            registry.register(tool)

    def test_policy_failure(self) -> None:
        class BadPolicy(Policy):
            def next(self, state):
                raise RuntimeError("boom")

        agent = Agent(self.config, ToolRegistry(), BadPolicy(), NullMemory())
        result = agent.run("hello")
        self.assertFalse(result["ok"])
        self.assertEqual(result["trace"][-1]["tool"], "policy")
        self.assertEqual(result["trace"][-1]["args"], {})
        self.assertEqual(result["trace"][-1]["duration_ms"], 0.0)

    def test_policy_observe_failure(self) -> None:
        class BadObserve(Policy):
            def next(self, state):
                return Action("echo", {}) if not state.observations else None

            def observe(self, state, observation):
                raise RuntimeError("boom")

        registry = ToolRegistry()
        registry.register(Tool("echo", "", lambda args, state: {"ok": True}))
        agent = Agent(self.config, registry, BadObserve(), NullMemory())
        result = agent.run("hello")
        self.assertFalse(result["ok"])
        self.assertIn("policy observe failed", result["error"])
        self.assertEqual(result["trace"][-1]["tool"], "policy.observe")
        lines = Path(self.config.trace_path).read_text(encoding="utf-8").splitlines()
        self.assertEqual(json.loads(lines[-1])["tool"], "policy.observe")

    def test_trace_args_sanitized(self) -> None:
        class ArgsPolicy(Policy):
            def next(self, state):
                if state.observations:
                    return None
                return Action(
                    "echo",
                    {
                        "text": "x" * 1000,
                        "meta": {
                            "token": "nvapi-abcdef",
                            "nvapi-abcdef": "value",
                            "blob": "y" * 1000,
                        },
                    },
                )

        registry = ToolRegistry()
        registry.register(Tool("echo", "", lambda args, state: {"ok": True}))
        agent = Agent(self.config, registry, ArgsPolicy(), NullMemory())
        result = agent.run("hello")
        args = result["trace"][0]["args"]
        self.assertLessEqual(len(args["text"]), 203)
        self.assertEqual(args["meta"]["token"], "nvapi-REDACTED")
        self.assertEqual(args["meta"]["nvapi-REDACTED"], "value")
        self.assertTrue(args["meta"]["blob"].endswith("..."))


if __name__ == "__main__":
    unittest.main()
