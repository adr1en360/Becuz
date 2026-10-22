import type { Investigation } from "./investigation";

// The UI renders the Investigation JSON from the agent. Until POST /run exists, a development
// sample can be switched on with NEXT_PUBLIC_DEV_SAMPLE=1. It is never loaded otherwise.
export async function loadInvestigation(): Promise<Investigation | null> {
  if (process.env.NEXT_PUBLIC_DEV_SAMPLE !== "1") return null;
  const sample = await import("../../dev-sample/investigation.sample.json");
  return sample.default as unknown as Investigation;
}
