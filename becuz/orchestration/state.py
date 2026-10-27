"""Shared run state for one investigation. The claims themselves live in the World Model."""
from __future__ import annotations

from datetime import date
from typing import TypedDict


class InvestigationState(TypedDict, total=False):
    question: str
    period_start: date
    period_end: date
    days: int  # the period's length, 1 to metrics.MAX_DAYS; 7 unless the owner picks another
    tree: dict  # metrics.profit_tree output
    queue: list[str]  # causes still to test, most promising first
    current: str | None  # the cause being tested or re-tested
    recalled: dict[str, str]  # cause_id -> H-MEM memory id, for causes the owner confirmed before
    answer: dict  # a direct answer (answers.answer) when the question is not a why-question
    report: dict  # the Writer's Investigation JSON


def period(state: InvestigationState) -> str:
    return f"{state['period_start']}..{state['period_end']}"
