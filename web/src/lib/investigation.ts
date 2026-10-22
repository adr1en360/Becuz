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
export type BaselineStart = string;
export type BaselineEnd = string;
export type CurrentNgn = number;
export type BaselineNgn = number;
/**
 * current_ngn - baseline_ngn
 */
export type ChangeNgn = number;
export type ChangePct = number;
export type Direction = "down" | "up" | "flat";
export type Component = "net_sales" | "cogs" | "wastage" | "opex" | "leakage";
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
 * The tree node this cause explains
 */
export type Component1 = "net_sales" | "cogs" | "wastage" | "opex" | "leakage";
/**
 * Effect on profit this week; negative is a loss
 */
export type ImpactNgn = number;
/**
 * Evidence row whose value_ngn is the impact
 */
export type ImpactEvidenceId = string;
export type ShareOfChangePct1 = number;
/**
 * 1 = largest effect
 */
export type Rank = number;
export type Origin = "internal" | "external";
export type Nature = "actionable" | "temporary";
export type Confidence = number;
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
 * What would have disproved the cause, e.g. 'unit cost flat across the baseline weeks'
 */
export type Test = string;
export type EvidenceId1 = string;
/**
 * True if the cause survived the test
 */
export type Survived = boolean;
export type FalsifiedBy = FalsificationTest[];
/**
 * This week's profit without this cause: headline.current_ngn - impact_ngn
 */
export type CounterfactualNgn = number;
/**
 * Zetaris sources the evidence read
 */
export type DependsOnSources = ("pos_files" | "bank_files" | "books_files" | "context_files")[];
export type Retries = number;
export type Causes = Cause[];
export type CauseId1 = string;
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
export type CauseId2 = string;
export type Action1 = string;
export type WhatToDo = Action[];
export type CauseId3 = string;
export type Question1 = string;
export type OwnerQuestions = OwnerQuestion[];
export type Limitations = string[];
export type DurationS = number;
export type ZetarisQueries = number;
export type ModelCalls = number;
export type Retries1 = number;
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
  baseline_start: BaselineStart;
  baseline_end: BaselineEnd;
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
 * A supported cause. Rejected or unverified hypotheses go to ruled_out instead.
 */
export interface Cause {
  cause_id: CauseId;
  title: Title;
  status?: Status2;
  component: Component1;
  impact_ngn: ImpactNgn;
  impact_evidence_id: ImpactEvidenceId;
  share_of_change_pct: ShareOfChangePct1;
  rank: Rank;
  origin: Origin;
  nature: Nature;
  confidence: Confidence;
  evidence: Evidence;
  falsified_by: FalsifiedBy;
  counterfactual_ngn: CounterfactualNgn;
  depends_on_sources: DependsOnSources;
  retries?: Retries;
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
export interface RuledOut1 {
  cause_id: CauseId1;
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
  what_to_do: WhatToDo;
}
export interface Action {
  cause_id: CauseId2;
  action: Action1;
}
export interface OwnerQuestion {
  cause_id: CauseId3;
  question: Question1;
}
export interface Stats {
  duration_s: DurationS;
  zetaris_queries: ZetarisQueries;
  model_calls: ModelCalls;
  retries: Retries1;
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
