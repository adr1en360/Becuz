"use client";

import { useEffect, useState } from "react";
import type { TraceEvent } from "@/lib/api";
import { ArrowLeftIcon, PlayIcon, StopIcon } from "@solar-icons/react/outline";
import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct, formatRange } from "@/lib/format";
import { Breakdown } from "./breakdown";
import { CashSection } from "./cash-section";
import { CauseList } from "./cause-list";
import { Convergence } from "./convergence";
import { ExecutiveSummary } from "./executive-summary";
import { LiveTrace } from "./live-trace";
import { MemoryNote } from "./memory-note";
import { Divider, Receipt } from "./receipt";
import { RuledOut } from "./ruled-out";
import { Stamp } from "./stamp";
import { StepQuestion } from "./step-question";

export function Report({
  data,
  events,
  onReset,
}: {
  data: Investigation;
  events: TraceEvent[];
  onReset: () => void;
}) {
  const [replaying, setReplaying] = useState(false);
  const [replayIdx, setReplayIdx] = useState(0);

  // Replay animation timer
  useEffect(() => {
    if (!replaying) return;
    if (replayIdx >= events.length) {
      const timer = setTimeout(() => setReplaying(false), 2000);
      return () => clearTimeout(timer);
    }
    const interval = setTimeout(() => {
      setReplayIdx((prev) => prev + 1);
    }, 450);
    return () => clearTimeout(interval);
  }, [replaying, replayIdx, events.length]);

  const startReplay = () => {
    setReplayIdx(1);
    setReplaying(true);
  };

  const stopReplay = () => {
    setReplaying(false);
  };

  const gaps = data.cash_gaps ?? [];
  const gapIds = new Set(gaps.map((g) => g.cause_id));
  const cashQuestions = data.owner_questions.filter((q) => gapIds.has(q.cause_id));

  const changePct = data.headline.change_pct;
  const changePctStr =
    changePct != null
      ? `${changePct < 0 ? "−" : "+"}${formatPct(changePct)}`
      : "";

  return (
    <div className="mx-auto w-full max-w-4xl flex-1 pb-24 pt-4">
      {/* Top action row */}
      <div className="mb-6 flex items-center justify-between gap-4 print:hidden">
        <button
          type="button"
          onClick={onReset}
          className="inline-flex h-9 items-center gap-2 rounded-full border border-desk-line px-4 text-xs font-semibold text-paper transition-colors hover:bg-paper hover:text-ink active:scale-95"
        >
          <ArrowLeftIcon size={14} aria-hidden />
          Ask another question
        </button>

        {replaying ? (
          <button
            type="button"
            onClick={stopReplay}
            className="inline-flex h-9 items-center gap-2 rounded-full bg-accent px-4 text-xs font-bold text-paper transition-colors hover:bg-paper hover:text-ink active:scale-95"
          >
            <StopIcon size={14} aria-hidden />
            Stop replay
          </button>
        ) : (
          events.length > 0 && (
            <button
              type="button"
              onClick={startReplay}
              className="inline-flex h-9 items-center gap-2 rounded-full border border-desk-line bg-desk-2 px-4 text-xs font-bold text-paper transition-colors hover:bg-paper hover:text-ink active:scale-95"
            >
              <PlayIcon size={14} aria-hidden />
              Play investigation
            </button>
          )
        )}
      </div>

      {replaying ? (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between rounded-2xl border border-flare bg-flare/10 px-4 py-2.5 text-xs font-mono text-paper">
            <span>Replaying investigation steps ({Math.min(replayIdx, events.length)} of {events.length})</span>
            <button type="button" onClick={stopReplay} className="text-flare underline hover:text-paper">
              Skip to full report
            </button>
          </div>
          <LiveTrace events={events.slice(0, replayIdx)} busy={replayIdx < events.length} />
        </div>
      ) : (
        <Receipt>
          {/* Header */}
          <div className="flex flex-col items-center gap-2 text-center">
            <span className="font-display text-3xl font-extrabold tracking-tight [font-stretch:125%]">
              Becuz<span className="text-accent">.</span>
            </span>
            <p className="font-mono text-xs uppercase tracking-[0.18em]">Profit investigation</p>
            <p className="font-mono text-xs text-muted">
              {formatRange(data.frame.period_start, data.frame.period_end)}
            </p>
            <div className="mt-1 flex flex-wrap items-center justify-center gap-2">
              {data.synthetic && <Stamp label="Synthetic data" rotate={-2} />}
              {data.mode === "sample" && <Stamp label="Sample mode" tone="accent" rotate={2} />}
            </div>

            {/* One strong change line: −36.3% · ₦379,412 → ₦241,717 */}
            <div className="mt-4 flex flex-col items-center gap-1 rounded-2xl bg-paper-2/60 px-6 py-4">
              <span className="font-mono text-xs uppercase tracking-wider text-muted">Profit change</span>
              <p className="num font-display text-3xl font-extrabold tracking-tight text-ink [font-stretch:115%] sm:text-4xl">
                <span className={data.headline.change_ngn < 0 ? "text-accent" : "text-ink"}>
                  {changePctStr}
                </span>{" "}
                · {formatNaira(data.headline.baseline_ngn)} → {formatNaira(data.headline.current_ngn)}
              </p>
            </div>

            {/* Replay button in header */}
            {events.length > 0 && (
              <button
                type="button"
                onClick={startReplay}
                className="mt-3 inline-flex items-center gap-2 rounded-full border border-ink/30 px-4 py-1.5 font-mono text-xs font-semibold text-ink transition-colors hover:bg-ink hover:text-paper active:scale-95 print:hidden"
              >
                <PlayIcon size={14} aria-hidden />
                Play investigation
              </button>
            )}
          </div>

          {data.status !== "complete" && (
            <section role="alert" className="mt-6 rounded-2xl border-2 border-accent px-5 py-4">
              <h2 className="font-semibold text-accent">This run is {data.status}.</h2>
              <ul className="mt-2 list-disc pl-5 text-sm text-muted">
                {data.errors?.map((error) => (
                  <li key={error}>{error}</li>
                ))}
              </ul>
            </section>
          )}

          {data.memory && data.memory.length > 0 && (
            <div className="mt-6">
              <MemoryNote entries={data.memory} />
            </div>
          )}

          <Divider />

          {/* Numbered Steps */}
          <div className="flex flex-col gap-6">
            <h2 className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-muted">
              Investigation steps
            </h2>

            {/* Step 1: The question */}
            <StepQuestion data={data} />

            {/* Step 2: Where the money went */}
            <Breakdown tree={data.tree} />

            {/* Steps 3..n: Supported causes (largest first) */}
            <CauseList causes={data.causes} runId={data.run_id} startStep={3} />

            {/* Struck-through Ruled Out items */}
            {data.ruled_out.length > 0 && <RuledOut items={data.ruled_out} />}

            {/* Money missing (cash gap kept separate from profit) */}
            {gaps.length > 0 && (
              <CashSection
                runId={data.run_id}
                gaps={gaps}
                lines={data.summary.cash ?? []}
                questions={cashQuestions}
              />
            )}

            {/* Convergence */}
            <Convergence
              convergence={data.convergence}
              change={data.headline.change_ngn}
              causes={data.causes}
              notTested={data.not_tested}
            />
          </div>

          <Divider />

          {/* Executive summary at end of page */}
          <ExecutiveSummary data={data} />
        </Receipt>
      )}
    </div>
  );
}
