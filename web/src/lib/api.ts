import type { Investigation } from "./investigation";

const base = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export const apiBase = base;
export const SAMPLE_SCENARIOS = ["s01", "s02", "s03", "s04", "s05"] as const;

export type Health = { ok: boolean; sample: boolean };

export class ApiError extends Error {}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${base}${path}`, init);
  } catch {
    throw new ApiError(`Could not reach the agent at ${base}. Is the server running?`);
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(body?.error ?? `The agent answered with an error (${res.status}).`);
  return body as T;
}

export const getHealth = (signal?: AbortSignal) => call<Health>("/health", { signal });

export type TraceEvent = {
  timestamp: string;
  run_id: string;
  agent_name: string;
  action: string;
  input_summary: string;
  output_summary: string;
  target_agent: string | null;
  confidence: number | null;
  retry_count: number;
  status: string;
  engine?: string;
  model?: string;
  via?: string;
  plain?: string;
};

// "finished" is a run started from the command line: it has a trace but no job on the server.
export type RunState = {
  run_id: string;
  status: "running" | "complete" | "failed" | "finished";
  events: TraceEvent[];
  report?: Investigation;
  error?: string;
};

const json = (body: unknown, signal?: AbortSignal): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
  signal,
});

export const startRun = (
  request: { question: string; scenario?: string; days?: number; period_start?: string },
  signal?: AbortSignal,
) =>
  call<{ run_id: string }>("/runs", json(request, signal));

export const getRun = (runId: string, signal?: AbortSignal) => call<RunState>(`/runs/${runId}`, { signal });

export const confirmCause = (runId: string, causeId: string) =>
  call<{ ok: boolean; memory_id: string }>("/confirm", json({ run_id: runId, cause_id: causeId }));
