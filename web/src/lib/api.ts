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

export function runInvestigation(request: { question: string; scenario?: string }, signal?: AbortSignal) {
  return call<Investigation>("/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });
}
