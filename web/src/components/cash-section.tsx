"use client";

import { AltArrowDownIcon } from "@solar-icons/react/outline";
import type { Investigation } from "@/lib/investigation";
import { formatNaira } from "@/lib/format";
import { ConfirmButton } from "./confirm-button";
import { SourceChips } from "./source-chips";
import { Stamp } from "./stamp";

type Props = {
  runId: string;
  gaps: NonNullable<Investigation["cash_gaps"]>;
  lines: string[];
  questions: Investigation["owner_questions"];
};

export function CashSection({ runId, gaps, lines, questions }: Props) {
  if (gaps.length === 0 && lines.length === 0) return null;

  return (
    <article className="rounded-2xl border-2 border-accent/40 bg-paper p-5 sm:p-6">
      <div className="flex items-start gap-4">
        <span
          aria-label="Money missing"
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-accent font-mono text-sm font-bold text-paper"
        >
          ₦
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%]">
              Money missing from the bank
            </h3>
            <Stamp label="Cash gap" tone="accent" rotate={-2} />
          </div>

          <p className="mt-1 text-sm font-medium text-accent">
            Kept apart from profit: sales occurred at the till, but cash never reached your bank account.
          </p>

          {lines.map((line) => (
            <p key={line} className="mt-3 text-sm leading-relaxed text-ink">
              {line}
            </p>
          ))}

          <div className="mt-5 flex flex-col gap-6">
            {gaps.map((gap) => (
              <div key={gap.cause_id} className="rounded-xl border border-rule bg-paper-2/40 p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <h4 className="font-display font-bold text-ink">{gap.title}</h4>
                  <span className="num font-mono text-xl font-bold text-accent">
                    {formatNaira(gap.impact_ngn)} missing
                  </span>
                </div>

                <div className="mt-3">
                  <SourceChips evidence={gap.evidence} />
                </div>

                <div className="mt-3">
                  <ConfirmButton runId={runId} causeId={gap.cause_id} />
                </div>

                <details className="group mt-4 border-t border-rule/60 pt-2">
                  <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
                    <span>Technical details</span>
                    <AltArrowDownIcon
                      size={14}
                      className="transition-transform duration-200 group-open:rotate-180"
                      aria-hidden
                    />
                  </summary>
                  <div className="mt-2 font-mono text-xs text-muted">
                    <p className="font-semibold text-ink">
                      Data source: Zetaris USL table becuz.transfer_check
                    </p>
                    <p className="mt-1">
                      Zetaris joins till transfer records with bank statement credits and flags uncredited sales.
                    </p>
                  </div>
                </details>
              </div>
            ))}
          </div>

          {questions.length > 0 && (
            <div className="mt-6 rounded-2xl border border-dashed border-ink/40 bg-paper-2 p-4 text-ink">
              <h4 className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-muted">
                Question for the owner
              </h4>
              <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm">
                {questions.map((q) => (
                  <li key={q.question} className="font-medium">
                    {q.question}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
