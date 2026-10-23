"""Shared run state for one investigation. The claims themselves live in the World Model."""
from __future__ import annotations

from datetime import date
from typing import TypedDict


class InvestigationState(TypedDict, total=False):
    question: str
    week_start: date
    week_end: date
    tree: dict  # metrics.profit_tree output
    queue: list[str]  # causes still to test, most promising first
    current: str | None  # the cause being tested or re-tested
    report: dict  # the Writer's Investigation JSON


def period(state: InvestigationState) -> str:
    return f"{state['week_start']}..{state['week_end']}"
