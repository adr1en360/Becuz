"""Shared state for one investigation. All four agents read and write it through LangGraph."""
from __future__ import annotations

from datetime import date
from typing import TypedDict


class Claim(TypedDict):
    """One entry in the shared claims list: the Investigator writes it, the Checker marks it."""

    cause_id: str
    status: str  # open, sent_back, supported, rejected, not_tested
    effect_ngn: float | None
    row_ids: list[str]
    effect_sql: str
    records_sql: str
    retries: int
    check: dict | None  # the Checker's re-run: match, rerun_value_ngn, note
    reason: str


class InvestigationState(TypedDict, total=False):
    question: str
    week_start: date
    week_end: date
    tree: dict  # metrics.profit_tree output
    queue: list[str]  # causes still to test, most promising first
    current: str | None
    claims: dict[str, Claim]
    report: dict  # the Writer's Investigation JSON
