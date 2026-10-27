"use client";

import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct, formatSigned } from "@/lib/format";
import { useSeen } from "@/lib/use-seen";
import { AltArrowDownIcon } from "@solar-icons/react/outline";
import { Leader } from "./receipt";

type Props = {
  convergence: Investigation["convergence"];
  change: number;
  causes: Investigation["causes"];
  notTested: string[];
};

function CauseNames({ causes }: { causes: Investigation["causes"] }) {
  if (causes.length === 0) return <p className="mt-1 text-sm text-muted">None in this period</p>;
  return (
    <ul className="mt-1.5 flex flex-col gap-1 text-sm font-semibold text-ink">
      {causes.map((c) => <li key={c.cause_id}>{c.title}</li>)}
    </ul>
  );
}

export function Convergence({ convergence, change, causes, notTested }: Props) {
  const { explained_ngn, explained_pct, unexplained_ngn } = convergence;
  const [ref, seen] = useSeen<HTMLDivElement>();
  const filled = Math.min(100, Math.max(0, explained_pct));

  // Grouped by tag, by name only: the UI never adds naira up, so the totals stay with the agent.
  const actionable = causes.filter((c) => c.nature === "actionable");
  const temporary = causes.filter((c) => c.nature === "temporary");

  const plainExplanation =
    explained_pct >= 95
      ? "These causes explain all of the change."
      : `These causes explain ${formatPct(explained_pct)} of the change.`;

  return (
    <article className="rounded-2xl border border-rule bg-paper p-5 sm:p-6">
      <div className="flex items-start gap-4">
        <span
          aria-label="Convergence"
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-sm font-bold text-paper"
        >
          Σ
        </span>

        <div className="min-w-0 flex-1">
          <h3 className="font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%]">
            How much is explained
          </h3>

          <p className="mt-2 text-base font-semibold text-ink">{plainExplanation}</p>

          {/* Split by tag: what you can act on vs what is likely to pass */}
          {causes.length > 0 && (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-rule bg-paper-2/50 p-3.5">
                <span className="font-mono text-xs uppercase tracking-wider text-muted">You can act on it</span>
                <CauseNames causes={actionable} />
              </div>

              <div className="rounded-xl border border-rule bg-paper-2/50 p-3.5">
                <span className="font-mono text-xs uppercase tracking-wider text-muted">Likely to pass</span>
                <CauseNames causes={temporary} />
              </div>
            </div>
          )}

          {/* Progress bar */}
          <div ref={ref} className="mt-5 h-2.5 w-full rounded-full bg-rule" aria-hidden>
            <div
              data-seen={seen}
              className="draw h-full rounded-full bg-ink"
              style={{ width: `${filled}%` }}
            />
          </div>
          <div className="mt-1.5 flex justify-between font-mono text-xs text-muted">
            <span>{formatPct(explained_pct)} explained</span>
            <span>{unexplained_ngn === 0 ? "0 unexplained" : `${formatNaira(unexplained_ngn)} unexplained`}</span>
          </div>

          <details className="group mt-5 border-t border-rule/60 pt-3">
            <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
              <span>Technical figures</span>
              <AltArrowDownIcon
                size={14}
                className="transition-transform duration-200 group-open:rotate-180"
                aria-hidden
              />
            </summary>
            <div className="mt-3 flex flex-col gap-1.5 rounded-xl bg-paper-2 p-3 font-mono text-xs text-muted">
              <Leader label="Headline change" value={formatSigned(change)} />
              <Leader label="Sum of explained causes" value={formatSigned(explained_ngn)} />
              <Leader label="Unexplained residual" value={formatSigned(unexplained_ngn)} />
              {notTested.length > 0 && (
                <div className="mt-2 border-t border-rule pt-2">
                  <span className="font-semibold text-ink font-sans">Not tested in this run:</span>
                  <ul className="mt-1 list-disc space-y-1 pl-4 text-[11px]">
                    {notTested.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </details>
        </div>
      </div>
    </article>
  );
}
