"use client";

import { useEffect, useRef, useState } from "react";
import { apiBase, getHealth, getRun, startRun, type Health, type TraceEvent } from "@/lib/api";
import type { Investigation } from "@/lib/investigation";
import { Composer, type Period } from "./composer";
import { EmptyState } from "./empty-state";
import { LiveTrace } from "./live-trace";
import { Report } from "./report";

type Phase =
  | { kind: "idle" }
  | { kind: "running"; events: TraceEvent[] }
  | { kind: "done"; data: Investigation; events: TraceEvent[] }
  | { kind: "error"; message: string };

const POLL_MS = 2000;
const MAX_MISSED_POLLS = 4;

const sleep = (ms: number, signal: AbortSignal) =>
  new Promise<void>((resolve) => {
    const id = setTimeout(resolve, ms);
    signal.addEventListener("abort", () => (clearTimeout(id), resolve()), { once: true });
  });

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
    if (phase.kind === "done") {
      window.scrollTo({ top: 320, behavior: "smooth" });
    }
  }, [phase.kind]);

  async function run(question: string, scenario: string | undefined, period: Period) {
    abort.current?.abort();
    const controller = new AbortController();
    abort.current = controller;
    setPhase({ kind: "running", events: [] });
    let missed = 0;
    try {
      const { run_id } = await startRun({ question, scenario, ...period }, controller.signal);
      while (!controller.signal.aborted) {
        await sleep(POLL_MS, controller.signal);
        if (controller.signal.aborted) return;
        let state;
        try {
          state = await getRun(run_id, controller.signal);
          missed = 0;
        } catch (error) {
          if (controller.signal.aborted) return;
          if (++missed >= MAX_MISSED_POLLS) throw error;
          continue;
        }
        if (state.status === "failed") throw new Error(state.error ?? "The investigation failed.");
        if (state.status === "running") {
          setPhase({ kind: "running", events: state.events });
        } else if (state.report) {
          setPhase({ kind: "done", data: state.report, events: state.events });
          return;
        } else {
          throw new Error("The run ended without a report.");
        }
      }
    } catch (error) {
      if (controller.signal.aborted) return;
      setPhase({
        kind: "error",
        message: error instanceof Error ? error.message : "Something went wrong.",
      });
    }
  }

  const sample = typeof health === "object" && health !== null && health.sample;
  const live = typeof health === "object" && health !== null && !health.sample;
  const note =
    phase.kind === "running"
      ? live
        ? "A live run takes several minutes. Becuz queries your records and has a model check each cause. Please keep this page open."
        : "Running the investigation. The agent queries your records and checks each cause."
      : health === "unreachable"
        ? `The agent is not reachable at ${apiBase}. Start the server, then reload.`
        : sample
          ? "The agent is in sample mode: it runs on generated test data, not a real shop."
          : "Becuz reads your records and never changes them.";

  return (
    <div className="flex flex-1 flex-col">
      {/* A. The Ask (Stays fixed / sticky at top) */}
      <section
        aria-label="Investigation setup"
        className="sticky top-0 z-30 border-b border-desk-line bg-desk px-4 py-4 sm:px-8 print:hidden"
      >
        <div className="mx-auto w-full max-w-4xl">
          <Composer
            running={phase.kind === "running"}
            showScenario={sample}
            sampleMode={sample}
            alert={phase.kind === "error" ? phase.message : null}
            note={note}
            onSubmit={run}
          />
        </div>
      </section>

      {/* Main scrolling investigation pane */}
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8 sm:px-8">
        {phase.kind === "idle" && <EmptyState />}

        {phase.kind === "running" && (
          <div className="mx-auto w-full max-w-2xl py-4">
            <LiveTrace events={phase.events} busy />
          </div>
        )}

        {phase.kind === "done" && (
          <Report
            data={phase.data}
            events={phase.events}
            onReset={() => setPhase({ kind: "idle" })}
          />
        )}
      </main>
    </div>
  );
}
