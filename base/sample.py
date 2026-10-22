from __future__ import annotations

from .providers import Completion


def rows(sql: str) -> list[list]:
    text = (sql or "").upper()
    if "SHOW LIGHTNING DATABASES" in text:
        return [["SAMPLE_DB", "Sample data", "3"]]
    if "SELECT 1" in text:
        return [[1]]
    return [["sample", 1], ["sample", 2], ["sample", 3]]


def answer(prompt: str) -> str:
    text = (prompt or "").strip()
    if "single word: ready" in text.lower():
        return "ready"
    return f"Sample mode. No provider call was made. Request: {text[:120]}"


def completion(messages: list[dict]) -> Completion:
    prompt = ""
    for message in reversed(messages or []):
        if message.get("role") == "user":
            prompt = str(message.get("content", ""))
            break
    return Completion(
        text=answer(prompt),
        provider="sample",
        model="sample",
        via="sample",
    )
