/* Generated from docs/investigation.schema.json by npm run types. Do not edit by hand. */

export type RunId = string;
export type Status = "complete" | "partial" | "failed";
export type Errors = string[];
export type Mode = "live" | "sample";
/**
 * True when the shop data is generated test data
 */
export type Synthetic = boolean;
/**
 * Synthetic scenario id, e.g. s01
 */
export type Scenario = string | null;
export type Question = string;
export type Metric = "profit";
export type PeriodStart = string;
export type PeriodEnd = string;
/**
 * The period's length in days, 1 to 28
 */
export type Days = number;
/**
 * First day of the earliest baseline window
 */
export type BaselineStart = string;
/**
 * Last day of the latest baseline window
 */
export type BaselineEnd = string;
/**
 * What the period is compared with, in the owner's words
 */
export type Baseline = string;
export type CurrentNgn = number;
export type BaselineNgn = number;
/**
 * current_ngn - baseline_ngn
 */
export type ChangeNgn = number;
/**
 * None when the baseline profit is zero
 */
export type ChangePct = number | null;
export type Direction = "down" | "up" | "flat";
export type Component = "net_sales" | "cogs" | "wastage" | "opex";
export type CurrentNgn1 = number;
export type BaselineNgn1 = number;
/**
 * current - baseline for this component (a cost rise is positive)
 */
export type ChangeNgn1 = number;
/**
 * Effect on profit: equals change_ngn for net_sales, minus change_ngn for costs
 */
export type ProfitEffectNgn = number;
/**
 * profit_effect_ngn as a percentage of the headline change
 */
export type ShareOfChangePct = number;
export type Status1 = "explained" | "partly_explained" | "unexplained" | "no_change";
export type Tree = TreeNode[];
export type CauseId = string;
export type Title = string;
export type Status2 = "supported";
/**
 * Naira in the period; negative is a loss
 */
export type ImpactNgn = number;
/**
 * Evidence row whose value_ngn is the impact
 */
export type ImpactEvidenceId = string;
/**
 * The model's rating of the evidence; None if it was unavailable
 */
export type Confidence = number | null;
/**
 * @minItems 1
 */
export type Evidence = [Evidence1, ...Evidence1[]];
export type EvidenceId = string;
/**
 * USL table the query read, e.g. becuz.supplier_invoices
 */
export type Table = string;
export type Sql = string;
/**
 * Record IDs behind the number
 */
export type RowIds = string[];
export type ValueNgn = number | null;
export type Summary = string;
export type Via = "zetaris" | "local";
export type Match = boolean;
export type RerunValueNgn = number | null;
export type Note = string;
/**
 * Model that judged the evidence, as reported by Nightshift
 */
export type Model = string | null;
/**
 * nightshift or sample-rules
 */
export type Via1 = string;
export type Signed = boolean;
/**
 * What would have disproved the cause, e.g. 'unit cost flat across the baseline'
 */
export type Test = string;
export type EvidenceId1 = string;
/**
 * True if the cause survived the test
 */
export type Survived = boolean;
export type FalsifiedBy = FalsificationTest[];
/**
 * Zetaris sources the evidence read
 */
export type DependsOnSources = ("pos_files" | "bank_files" | "books_files" | "context_files")[];
export type Retries = number;
/**
 * The tree node this cause explains
 */
export type Component1 = "net_sales" | "cogs" | "wastage" | "opex";
export type ShareOfChangePct1 = number;
/**
 * 1 = largest effect
 */
export type Rank = number;
export type Origin = "internal" | "external";
export type Nature = "actionable" | "temporary";
/**
 * This week's profit without this cause: headline.current_ngn - impact_ngn
 */
export type CounterfactualNgn = number;
export type Causes = Cause[];
export type CauseId1 = string;
export type Title1 = string;
export type Status3 = "supported";
/**
 * Naira in the period; negative is a loss
 */
export type ImpactNgn1 = number;
/**
 * Evidence row whose value_ngn is the impact
 */
export type ImpactEvidenceId1 = string;
/**
 * The model's rating of the evidence; None if it was unavailable
 */
export type Confidence1 = number | null;
/**
 * @minItems 1
 */
export type Evidence2 = [Evidence1, ...Evidence1[]];
export type FalsifiedBy1 = FalsificationTest[];
/**
 * Zetaris sources the evidence read
 */
export type DependsOnSources1 = ("pos_files" | "bank_files" | "books_files" | "context_files")[];
export type Retries1 = number;
export type CashGaps = CashGap[];
export type CauseId2 = string;
/**
 * When the owner confirmed it (ISO timestamp)
 */
export type ConfirmedAt = string;
/**
 * True if it was found again, False if not, None if this period could not test it
 */
export type HeldAgain = boolean | null;
/**
 * H-MEM confidence in the memory before this run
 */
export type ConfidenceBefore = number;
/**
 * H-MEM confidence after this run's result
 */
export type ConfidenceAfter = number;
/**
 * Plain-language line for the owner
 */
export type Message = string;
/**
 * Owner-confirmed causes recalled from H-MEM for this run
 */
export type Memory = Recall[];
export type CauseId3 = string;
export type Hypothesis = string;
export type Reason = string;
export type TestedValueNgn = number | null;
export type EvidenceId2 = string | null;
export type RuledOut = RuledOut1[];
/**
 * Possible causes the run did not test, and why
 */
export type NotTested = string[];
/**
 * Sum of supported causes' impact_ngn
 */
export type ExplainedNgn = number;
export type ExplainedPct = number;
/**
 * headline.change_ngn - explained_ngn
 */
export type UnexplainedNgn = number;
export type WhatHappened = string;
export type Why = string[];
/**
 * One line per cash gap, kept apart from profit
 */
export type Cash = string[];
/**
 * What acting on the findings is worth, from the measured figures only; never a forecast
 */
export type Outcome = string;
export type CauseId4 = string;
export type Action1 = string;
export type WhatToDo = Action[];
export type CauseId5 = string;
export type Question1 = string;
export type OwnerQuestions = OwnerQuestion[];
export type Limitations = string[];
export type DurationS = number;
export type ZetarisQueries = number;
export type ModelCalls = number;
export type Retries2 = number;
export type TraceFile = string;

export interface Investigation {
  run_id: RunId;
  status: Status;
  errors?: Errors;
  mode: Mode;
  synthetic: Synthetic;
  scenario?: Scenario;
  frame: Frame;
  headline: Headline;
  tree: Tree;
  causes: Causes;
  cash_gaps?: CashGaps;
  memory?: Memory;
  ruled_out: RuledOut;
  not_tested: NotTested;
  convergence: Convergence;
  summary: Summary1;
  owner_questions: OwnerQuestions;
  limitations: Limitations;
  stats: Stats;
  trace_file: TraceFile;
}
export interface Frame {
  question: Question;
  metric?: Metric;
  period_start: PeriodStart;
  period_end: PeriodEnd;
  days?: Days;
  baseline_start: BaselineStart;
  baseline_end: BaselineEnd;
  baseline?: Baseline;
}
export interface Headline {
  current_ngn: CurrentNgn;
  baseline_ngn: BaselineNgn;
  change_ngn: ChangeNgn;
  change_pct: ChangePct;
  direction: Direction;
}
export interface TreeNode {
  component: Component;
  current_ngn: CurrentNgn1;
  baseline_ngn: BaselineNgn1;
  change_ngn: ChangeNgn1;
  profit_effect_ngn: ProfitEffectNgn;
  share_of_change_pct: ShareOfChangePct;
  status: Status1;
}
/**
 * A supported cause of the profit change; impact_ngn is its effect on the period's profit.
 */
export interface Cause {
  cause_id: CauseId;
  title: Title;
  status?: Status2;
  impact_ngn: ImpactNgn;
  impact_evidence_id: ImpactEvidenceId;
  confidence: Confidence;
  evidence: Evidence;
  falsified_by: FalsifiedBy;
  depends_on_sources: DependsOnSources;
  retries?: Retries;
  component: Component1;
  share_of_change_pct: ShareOfChangePct1;
  rank: Rank;
  origin: Origin;
  nature: Nature;
  counterfactual_ngn: CounterfactualNgn;
}
export interface Evidence1 {
  evidence_id: EvidenceId;
  table: Table;
  sql: Sql;
  row_ids: RowIds;
  value_ngn?: ValueNgn;
  summary: Summary;
  via: Via;
  check?: Check | null;
}
/**
 * The Checker's independent re-run of an evidence query, and its verdict.
 */
export interface Check {
  match: Match;
  rerun_value_ngn?: RerunValueNgn;
  note?: Note;
  model?: Model;
  via: Via1;
  signed?: Signed;
}
export interface FalsificationTest {
  test: Test;
  evidence_id: EvidenceId1;
  survived: Survived;
}
/**
 * Money the till recorded but the bank never received; impact_ngn is the missing amount (negative).
 * It is cash the shop is owed, so it is not part of the profit change.
 */
export interface CashGap {
  cause_id: CauseId1;
  title: Title1;
  status?: Status3;
  impact_ngn: ImpactNgn1;
  impact_evidence_id: ImpactEvidenceId1;
  confidence: Confidence1;
  evidence: Evidence2;
  falsified_by: FalsifiedBy1;
  depends_on_sources: DependsOnSources1;
  retries?: Retries1;
}
/**
 * A cause the owner confirmed in an earlier run, recalled from H-MEM and tested first.
 */
export interface Recall {
  cause_id: CauseId2;
  confirmed_at: ConfirmedAt;
  held_again: HeldAgain;
  confidence_before: ConfidenceBefore;
  confidence_after: ConfidenceAfter;
  message: Message;
}
export interface RuledOut1 {
  cause_id: CauseId3;
  hypothesis: Hypothesis;
  reason: Reason;
  tested_value_ngn?: TestedValueNgn;
  evidence_id?: EvidenceId2;
}
export interface Convergence {
  explained_ngn: ExplainedNgn;
  explained_pct: ExplainedPct;
  unexplained_ngn: UnexplainedNgn;
}
export interface Summary1 {
  what_happened: WhatHappened;
  why: Why;
  cash?: Cash;
  outcome?: Outcome;
  what_to_do: WhatToDo;
}
export interface Action {
  cause_id: CauseId4;
  action: Action1;
}
export interface OwnerQuestion {
  cause_id: CauseId5;
  question: Question1;
}
export interface Stats {
  duration_s: DurationS;
  zetaris_queries: ZetarisQueries;
  model_calls: ModelCalls;
  retries: Retries2;
  models: Models;
  via: Via2;
}
/**
 * Model name -> number of requests it handled
 */
export interface Models {
  [k: string]: number;
}
/**
 * Route -> count, e.g. nightshift, zetaris, local, sample-rules
 */
export interface Via2 {
  [k: string]: number;
}
