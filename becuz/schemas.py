"""The Investigation JSON: what one Becuz run returns, and what the UI renders.

Units: every *_ngn field is naira for the investigated week (a one-week period),
compared with the average week of the 4 weeks before it. Every *_pct field is a
percentage from 0 to 100; confidence is a fraction from 0 to 1. A negative
profit effect is a loss.

Money comes from SQL, never from the model. The validators below tie each
cause's impact to an evidence row and recompute every derived figure, so a
report whose numbers don't add up cannot be built.

Export the JSON Schema for the UI with:

    uv run python -m becuz.schemas > docs/investigation.schema.json
"""
from __future__ import annotations

import json
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Source = Literal["pos_files", "bank_files", "books_files", "context_files"]
Component = Literal["net_sales", "cogs", "wastage", "opex", "leakage"]  # metrics.py names without "_ngn"
TOLERANCE_NGN = 1.0
MIN_EFFECT_NGN = 1000.0  # smaller effects are noise, so a cause below this can't be supported


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
    change_ngn: float = Field(description="current_ngn - baseline_ngn")
    change_pct: float | None = Field(description="None when the baseline profit is zero")
    direction: Literal["down", "up", "flat"]


class TreeNode(Model):
    component: Component
    current_ngn: float
    baseline_ngn: float
    change_ngn: float = Field(description="current - baseline for this component (a cost rise is positive)")
    profit_effect_ngn: float = Field(description="Effect on profit: equals change_ngn for net_sales, minus change_ngn for costs")
    share_of_change_pct: float = Field(description="profit_effect_ngn as a percentage of the headline change")
    status: Literal["explained", "partly_explained", "unexplained", "no_change"]


class Check(Model):
    """The Checker's independent re-run of an evidence query, and its verdict."""

    match: bool
    rerun_value_ngn: float | None = None
    note: str = ""
    model: str | None = Field(default=None, description="Model that judged the evidence, as reported by Nightshift")
    via: str = Field(description="nightshift or sample-rules")
    signed: bool = False


class Evidence(Model):
    evidence_id: str
    table: str = Field(description="USL table the query read, e.g. becuz.supplier_invoices")
    sql: str
    row_ids: list[str] = Field(description="Record IDs behind the number")
    value_ngn: float | None = None
    summary: str
    via: Literal["zetaris", "local"]
    check: Check | None = None


class FalsificationTest(Model):
    test: str = Field(description="What would have disproved the cause, e.g. 'unit cost flat across the baseline weeks'")
    evidence_id: str
    survived: bool = Field(description="True if the cause survived the test")


class Cause(Model):
    """A supported cause. Rejected or unverified hypotheses go to ruled_out instead."""

    cause_id: str
    title: str
    status: Literal["supported"] = "supported"
    component: Component = Field(description="The tree node this cause explains")
    impact_ngn: float = Field(description="Effect on profit this week; negative is a loss")
    impact_evidence_id: str = Field(description="Evidence row whose value_ngn is the impact")
    share_of_change_pct: float
    rank: int = Field(ge=1, description="1 = largest effect")
    origin: Literal["internal", "external"]
    nature: Literal["actionable", "temporary"]
    confidence: float | None = Field(ge=0, le=1, description="The model's rating of the evidence; None if it was unavailable")
    evidence: list[Evidence] = Field(min_length=1)
    falsified_by: list[FalsificationTest]
    counterfactual_ngn: float = Field(description="This week's profit without this cause: headline.current_ngn - impact_ngn")
    depends_on_sources: list[Source] = Field(description="Zetaris sources the evidence read")
    retries: int = 0

    @model_validator(mode="after")
    def impact_comes_from_evidence(self) -> Cause:
        source = {e.evidence_id: e for e in self.evidence}.get(self.impact_evidence_id)
        if source is None or source.value_ngn is None:
            raise ValueError(f"{self.cause_id}: impact must point at an evidence row with a value")
        if abs(source.value_ngn - self.impact_ngn) > TOLERANCE_NGN:
            raise ValueError(f"{self.cause_id}: impact {self.impact_ngn} differs from its evidence {source.value_ngn}")
        if abs(self.impact_ngn) < MIN_EFFECT_NGN:
            raise ValueError(f"{self.cause_id}: effect {self.impact_ngn} is below {MIN_EFFECT_NGN}, too small to support")
        if not any(e.row_ids for e in self.evidence):
            raise ValueError(f"{self.cause_id}: a supported cause needs record IDs")
        return self


class RuledOut(Model):
    cause_id: str
    hypothesis: str
    reason: str
    tested_value_ngn: float | None = None
    evidence_id: str | None = None


class Convergence(Model):
    explained_ngn: float = Field(description="Sum of supported causes' impact_ngn")
    explained_pct: float
    unexplained_ngn: float = Field(description="headline.change_ngn - explained_ngn")


class Action(Model):
    cause_id: str
    action: str


class Summary(Model):
    what_happened: str
    why: list[str]
    what_to_do: list[Action]


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
    status: Literal["complete", "partial", "failed"]
    errors: list[str] = []
    mode: Literal["live", "sample"]
    synthetic: bool = Field(description="True when the shop data is generated test data")
    scenario: str | None = Field(default=None, description="Synthetic scenario id, e.g. s01")
    frame: Frame
    headline: Headline
    tree: list[TreeNode]
    causes: list[Cause]
    ruled_out: list[RuledOut]
    not_tested: list[str] = Field(description="Possible causes the run did not test, and why")
    convergence: Convergence
    summary: Summary
    owner_questions: list[OwnerQuestion]
    limitations: list[str]
    stats: Stats
    trace_file: str

    @model_validator(mode="after")
    def figures_add_up(self) -> Investigation:
        h, c = self.headline, self.convergence
        explained = sum(cause.impact_ngn for cause in self.causes)
        checks = {
            "headline change": (h.change_ngn, h.current_ngn - h.baseline_ngn),
            "explained": (c.explained_ngn, explained),
            "unexplained": (c.unexplained_ngn, h.change_ngn - explained),
        }
        checks.update({f"{cause.cause_id} counterfactual": (cause.counterfactual_ngn, h.current_ngn - cause.impact_ngn)
                       for cause in self.causes})
        wrong = [name for name, (given, expected) in checks.items() if abs(given - expected) > TOLERANCE_NGN]
        if wrong:
            raise ValueError("figures do not add up: " + ", ".join(wrong))
        return self


if __name__ == "__main__":
    print(json.dumps(Investigation.model_json_schema(), indent=2))
