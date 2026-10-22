"""The Investigation JSON: what one Becuz run returns, and what the UI renders.

Every money field is in naira and comes from SQL, never from the model.
Export the JSON Schema for the UI with:

    uv run python -m becuz.schemas > docs/investigation.schema.json
"""
from __future__ import annotations

import json
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ClaimStatus = Literal["open", "supported", "rejected"]
Component = Literal["net_sales", "cogs", "wastage", "opex", "leakage"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a typo in a field name fails loudly


class Frame(Model):
    question: str
    metric: Literal["profit"] = "profit"
    period_start: date
    period_end: date
    baseline_start: date
    baseline_end: date


class Headline(Model):
    current_ngn: float
    baseline_ngn: float
    change_ngn: float
    change_pct: float


class TreeNode(Model):
    component: Component
    current_ngn: float
    baseline_ngn: float
    change_ngn: float
    share_of_change_pct: float = Field(description="This component's share of the profit change")
    status: Literal["explained", "partly_explained", "unexplained", "no_change"]


class Check(Model):
    """The Checker's independent re-run of an evidence query."""

    match: bool
    rerun_value_ngn: float | None = None
    note: str = ""


class Evidence(Model):
    evidence_id: str
    source: str = Field(description="USL table the query read, e.g. becuz.supplier_invoices")
    sql: str
    row_ids: list[str] = Field(description="Record IDs behind the number; a claim without them is rejected")
    value_ngn: float | None = None
    summary: str
    check: Check | None = None


class Cause(Model):
    cause_id: str
    title: str
    status: ClaimStatus
    impact_ngn: float = Field(description="Effect on profit this week; negative is a loss")
    share_of_drop_pct: float
    rank: int | None = Field(default=None, description="Set for supported causes, 1 = largest")
    origin: Literal["internal", "external"]
    nature: Literal["actionable", "temporary"]
    confidence: float = Field(ge=0, le=1)
    evidence: list[Evidence]
    falsified_by: list[str] = Field(description="Tests that could have disproved this cause, and what each found")
    counterfactual_ngn: float = Field(description="This week's profit if this cause had not happened")
    depends_on_sources: list[str] = Field(description="Zetaris sources the claim relies on, e.g. pos_files, bank_files")
    retries: int = 0
    recommendation: str = ""


class RuledOut(Model):
    cause_id: str
    hypothesis: str
    reason: str
    evidence_id: str | None = None


class Convergence(Model):
    explained_ngn: float
    explained_pct: float
    unexplained_ngn: float


class Summary(Model):
    what_happened: str
    why: list[str]
    what_to_do: list[str]


class OwnerQuestion(Model):
    cause_id: str
    question: str


class Stats(Model):
    duration_s: float
    zetaris_queries: int
    model_calls: int
    retries: int
    models: dict[str, int] = Field(description="Model name -> number of requests it handled")
    via: dict[str, int] = Field(description="Route -> count, e.g. nightshift, zetaris, local, sample-rules")


class Investigation(Model):
    run_id: str
    mode: Literal["live", "sample"]
    scenario: str | None = Field(default=None, description="Synthetic scenario id, e.g. s01")
    frame: Frame
    headline: Headline
    tree: list[TreeNode]
    causes: list[Cause]
    ruled_out: list[RuledOut]
    convergence: Convergence
    summary: Summary
    owner_questions: list[OwnerQuestion]
    limitations: list[str]
    stats: Stats
    trace_file: str


if __name__ == "__main__":
    print(json.dumps(Investigation.model_json_schema(), indent=2))
