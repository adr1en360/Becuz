import { AltArrowDownIcon } from "@solar-icons/react/outline";
import type { Investigation } from "@/lib/investigation";
import { formatNaira } from "@/lib/format";
import { Leader } from "./receipt";

type Answer = NonNullable<Investigation["answer"]>;

const kindLabel: Record<Answer["kind"], string> = {
  top_sellers: "What sold",
  totals: "Totals",
  expenses: "Biggest expenses",
  missing_money: "Missing money",
};

// A direct answer: one read-only query, its rows and the records behind them. No model is involved.
export function AnswerCard({ answer, step }: { answer: Answer; step: number }) {
  return (
    <article aria-labelledby="answer-heading" className="rounded-2xl border border-rule bg-paper p-5 sm:p-6">
      <div className="flex items-start gap-4">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-sm font-bold text-paper">
          {step}
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-muted">{kindLabel[answer.kind]}</p>
          <h3 id="answer-heading" className="mt-1 text-balance font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%]">
            {answer.sentence}
          </h3>

          {answer.rows.length > 0 && (
            <ol className="mt-5 flex flex-col gap-3">
              {answer.rows.map((row) => (
                <li key={row.label}>
                  <Leader label={row.label} value={formatNaira(row.value_ngn)} />
                  <p className="num mt-0.5 font-mono text-xs text-muted">
                    {row.detail}
                    {row.usual_ngn !== null && ` / usually ${formatNaira(row.usual_ngn)}`}
                  </p>
                </li>
              ))}
            </ol>
          )}

          <details className="group mt-5 border-t border-rule/60 pt-3">
            <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
              <span>Show the query</span>
              <AltArrowDownIcon size={14} className="transition-transform duration-200 group-open:rotate-180" aria-hidden />
            </summary>
            <pre
              tabIndex={0}
              role="group"
              aria-label="SQL query"
              className="mt-3 overflow-x-auto rounded-xl bg-ink p-4 font-mono text-[13px] leading-relaxed text-paper"
            >
              {answer.sql}
            </pre>
            {answer.row_ids.length > 0 && (
              <p className="mt-2 font-mono text-xs text-muted">
                {answer.row_ids.length} {answer.row_ids.length === 1 ? "record" : "records"} behind this answer
              </p>
            )}
          </details>
        </div>
      </div>
    </article>
  );
}
