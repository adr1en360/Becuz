import type { TraceEvent } from "./api";

const actionLabel: Record<string, string> = {
  scout_contract: "Scoped the question",
  recall: "Looked in memory",
  plan: "Planned the tests",
  test_cause: "Tested a cause",
  supported: "Accepted",
  rejected: "Rejected",
  judge: "Judged the evidence",
  markovian_summary: "Compressed its notes",
  write_report: "Wrote the report",
};

const engineLabel: Record<string, string> = {
  scout_intent: "Scout Intent",
  hmem: "H-MEM",
  world_model: "World Model",
  markovian: "Markovian",
};

const causeSteps = new Set(["test_cause", "supported", "rejected"]);

export const describeAction = (e: TraceEvent) => actionLabel[e.action] ?? e.action.replaceAll("_", " ");
export const engineName = (e: TraceEvent) => (e.engine ? (engineLabel[e.engine] ?? e.engine) : null);
export const causeName = (e: TraceEvent) => (causeSteps.has(e.action) ? e.input_summary.replaceAll("_", " ") : null);

export function secondsSince(first: TraceEvent | undefined, e: TraceEvent) {
  if (!first) return 0;
  return Math.max(0, Math.round((Date.parse(e.timestamp) - Date.parse(first.timestamp)) / 1000));
}
