"use client";

import type { Investigation } from "@/lib/investigation";
import { formatRange } from "@/lib/format";
import { AltArrowDownIcon } from "@solar-icons/react/outline";

export function StepQuestion({ data }: { data: Investigation }) {
  const { frame, run_id, mode, scenario } = data;

  return (
    <article className="rounded-2xl border border-rule bg-paper p-5 sm:p-6">
      <div className="flex items-start gap-4">
        <span
          aria-label="Step 1"
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-sm font-bold text-paper"
        >
          1
        </span>

        <div className="min-w-0 flex-1">
          <h3 className="font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%]">
            The question
          </h3>

          <p className="mt-2 text-base text-ink">
            You asked: <span className="font-semibold italic">“{frame.question}”</span>
          </p>

          <p className="mt-2 text-sm leading-relaxed text-muted">
            We investigated the period of{" "}
            <span className="font-semibold text-ink">
              {formatRange(frame.period_start, frame.period_end)}
            </span>{" "}
            and compared it with the 4 periods before (
            {formatRange(frame.baseline_start, frame.baseline_end)}).
          </p>

          <details className="group mt-4 border-t border-rule/60 pt-3">
            <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
              <span>Technical details</span>
              <AltArrowDownIcon
                size={14}
                className="transition-transform duration-200 group-open:rotate-180"
                aria-hidden
              />
            </summary>
            <div className="mt-2 rounded-xl bg-paper-2 p-3 font-mono text-xs text-muted">
              <p>Run ID: <span className="text-ink font-semibold">{run_id}</span></p>
              <p>Mode: <span className="text-ink">{mode}</span></p>
              {scenario && <p>Test scenario: <span className="text-ink">{scenario}</span></p>}
              <p>Metric: <span className="text-ink">{frame.metric ?? "profit"}</span></p>
            </div>
          </details>
        </div>
      </div>
    </article>
  );
}
