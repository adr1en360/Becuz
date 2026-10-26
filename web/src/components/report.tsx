import type { TraceEvent } from "@/lib/api";
import { ArrowLeftIcon } from "@solar-icons/react/outline";
import type { Investigation } from "@/lib/investigation";
import { formatRange } from "@/lib/format";
import { Breakdown } from "./breakdown";
import { CashSection } from "./cash-section";
import { CauseList } from "./cause-list";
import { Convergence } from "./convergence";
import { Headline } from "./headline";
import { MemoryNote } from "./memory-note";
import { NextSteps } from "./next-steps";
import { Divider, Receipt } from "./receipt";
import { RuledOut } from "./ruled-out";
import { RunDetails } from "./run-details";
import { TraceSection } from "./trace-section";
import { Stamp } from "./stamp";

export function Report({ data, events, onReset }: { data: Investigation; events: TraceEvent[]; onReset: () => void }) {
  const gaps = data.cash_gaps ?? [];
  const gapIds = new Set(gaps.map((g) => g.cause_id));
  const cashQuestions = data.owner_questions.filter((q) => gapIds.has(q.cause_id));
  const otherQuestions = data.owner_questions.filter((q) => !gapIds.has(q.cause_id));
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 pb-24 pt-4 sm:px-8">
      <div className="mx-auto max-w-[40rem]">
        <button
          type="button"
          onClick={onReset}
          className="mb-10 inline-flex h-10 items-center gap-2 rounded-full border border-desk-line px-4 text-sm font-semibold text-paper hover:bg-paper hover:text-ink"
        >
          <ArrowLeftIcon size={16} aria-hidden />
          Ask another question
        </button>
      </div>

      <Receipt>
        <div className="flex flex-col items-center gap-2 text-center">
          <span className="font-display text-3xl font-extrabold tracking-tight [font-stretch:125%]">
            Becuz<span className="text-accent">.</span>
          </span>
          <p className="font-mono text-xs uppercase tracking-[0.18em]">Profit investigation</p>
          <p className="font-mono text-xs text-muted">
            {formatRange(data.frame.period_start, data.frame.period_end)}
          </p>
          <div className="mt-2 flex flex-wrap items-center justify-center gap-3">
            {data.synthetic && <Stamp label="Synthetic data" rotate={-3} />}
            {data.mode === "sample" && <Stamp label="Sample mode" tone="accent" rotate={2} />}
          </div>
        </div>

        {data.status !== "complete" && (
          <section role="alert" className="mt-8 rounded-2xl border-2 border-accent px-5 py-4">
            <h2 className="font-semibold">This run is {data.status}.</h2>
            <ul className="mt-2 list-disc pl-5 text-muted">
              {data.errors?.map((error) => <li key={error}>{error}</li>)}
            </ul>
          </section>
        )}

        {data.memory && data.memory.length > 0 && <MemoryNote entries={data.memory} />}
        <Divider />
        <Headline data={data} />
        <Divider />
        <Breakdown tree={data.tree} />
        <Divider />
        <CauseList causes={data.causes} runId={data.run_id} />
        <Divider />
        {gaps.length > 0 && (
          <>
            <CashSection runId={data.run_id} gaps={gaps} lines={data.summary.cash ?? []} questions={cashQuestions} />
            <Divider />
          </>
        )}
        <RuledOut items={data.ruled_out} />
        <Divider />
        <Convergence convergence={data.convergence} change={data.headline.change_ngn} notTested={data.not_tested} />
        <Divider />
        <NextSteps data={data} questions={otherQuestions} />
        <Divider />
        {events.length > 0 && (
          <>
            <TraceSection events={events} traceFile={data.trace_file} />
            <Divider />
          </>
        )}
        <RunDetails data={data} />
      </Receipt>
    </main>
  );
}
