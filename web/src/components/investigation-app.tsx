"use client";

import { useEffect, useRef, useState } from "react";
import { apiBase, getHealth, runInvestigation, type Health } from "@/lib/api";
import type { Investigation } from "@/lib/investigation";
import { Composer } from "./composer";
import { EmptyState } from "./empty-state";
import { Report } from "./report";

type Phase = { kind: "idle" } | { kind: "running" } | { kind: "done"; data: Investigation } | { kind: "error"; message: string };

export function InvestigationApp() {
  const [health, setHealth] = useState<Health | null | "unreachable">(null);
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const abort = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then(setHealth)
      .catch(() => {
        if (!controller.signal.aborted) setHealth("unreachable");
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (phase.kind === "done") document.getElementById("headline")?.focus();
  }, [phase.kind]);

  async function run(question: string, scenario?: string) {
    abort.current?.abort();
    const controller = new AbortController();
    abort.current = controller;
    setPhase({ kind: "running" });
    try {
      const data = await runInvestigation({ question, scenario }, controller.signal);
      setPhase({ kind: "done", data });
    } catch (error) {
      if (controller.signal.aborted) return;
      setPhase({ kind: "error", message: error instanceof Error ? error.message : "Something went wrong." });
    }
  }

  if (phase.kind === "done") return <Report data={phase.data} onReset={() => setPhase({ kind: "idle" })} />;

  const sample = typeof health === "object" && health !== null && health.sample;
  const note =
    phase.kind === "running"
      ? "Running the investigation. The agent queries your records and checks each cause."
      : health === "unreachable"
        ? `The agent is not reachable at ${apiBase}. Start the server, then reload.`
        : sample
          ? "The agent is in sample mode: it runs on generated test weeks, not a real shop."
          : "Becuz reads your records and never changes them.";

  return (
    <EmptyState
      busy={phase.kind === "running"}
      alert={
        phase.kind === "error" ? (
          <p role="alert" className="rounded-2xl border border-flare px-4 py-3 text-sm">
            {phase.message}
          </p>
        ) : null
      }
      composer={<Composer running={phase.kind === "running"} showScenario={sample} note={note} onSubmit={run} />}
    />
  );
}
