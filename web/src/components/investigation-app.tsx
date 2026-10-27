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

  const pane = useRef<HTMLElement>(null);

  // The receipt pane scrolls on its own on wide screens; on phones it sits under the form, so bring it into view.
  useEffect(() => {
    const el = pane.current;
    if (!el || phase.kind === "idle" || phase.kind === "error") return;
    if (window.matchMedia("(min-width: 1024px)").matches) {
      if (phase.kind === "done") el.scrollTo({ top: 0 });
    } else {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
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
          ? "Sample mode: synthetic test shops, not a real one. Findings show correlation, not proven causation."
          : "Becuz reads your records and never changes them.";

  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(0,27rem)_minmax(0,1fr)] xl:grid-cols-[minmax(0,32rem)_minmax(0,1fr)] 2xl:grid-cols-[minmax(0,34rem)_minmax(0,1fr)]">
      <aside
        aria-label="Investigation setup"
        className="border-b border-desk-line px-4 py-6 sm:px-8 lg:overflow-y-auto lg:border-b-0 lg:border-r lg:py-8 lg:[@media(max-height:760px)]:py-4 print:hidden"
      >
        <div className="mx-auto flex max-w-xl flex-col gap-6 lg:max-w-none lg:gap-[clamp(0.9rem,2.4vh,2rem)]">
          <div className="flex flex-col gap-2">
            <h1 className="text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-[-0.02em] [font-stretch:125%] lg:[@media(max-height:760px)]:text-3xl lg:[@media(min-height:930px)]:text-[2.75rem]">
              Ask why your profit <span className="text-flare">moved.</span>
            </h1>
            <p className="text-desk-muted [@media(max-height:700px)]:hidden lg:[@media(min-height:930px)]:mt-2 lg:[@media(min-height:930px)]:text-lg">
              Answers from your till, bank, invoices and expenses, with the records behind them.
            </p>
          </div>
          <Composer
            running={phase.kind === "running"}
            showScenario={sample}
            sampleMode={sample}
            alert={phase.kind === "error" ? phase.message : null}
            note={note}
            onSubmit={run}
          />
        </div>
      </aside>

      <main ref={pane} aria-label="Receipt" className="dot-bg scroll-mt-2 lg:overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-8 lg:py-10">
          {(phase.kind === "idle" || phase.kind === "error") && <EmptyState />}
          {phase.kind === "running" && <LiveTrace events={phase.events} busy />}
          {phase.kind === "done" && <Report data={phase.data} events={phase.events} />}
        </div>
      </main>
    </div>
  );
}
