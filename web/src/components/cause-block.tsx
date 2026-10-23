import { AltArrowDownIcon, CheckCircleIcon, CloseCircleIcon } from "@solar-icons/react/bold";
import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct } from "@/lib/format";
import { natureLabel, originLabel, sourceLabel } from "@/lib/labels";
import { Stamp } from "./stamp";

type Cause = Investigation["causes"][number];

const pill = "rounded-full border border-ink/40 px-3 py-1 font-mono text-xs text-ink";

function checkedBy(check: NonNullable<Cause["evidence"][number]["check"]>) {
  const who = check.model ?? (check.via === "rules" || check.via === "sample-rules" ? "fixed rules" : check.via);
  return `${who}${check.signed ? ", signed" : ""}`;
}

export function CauseBlock({ cause, defaultOpen = false }: { cause: Cause; defaultOpen?: boolean }) {
  const loss = cause.impact_ngn < 0;
  const verified = cause.evidence.every((e) => e.check?.match);
  return (
    <article className="flex gap-4">
      <span
        aria-label={`Rank ${cause.rank}`}
        className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-sm font-medium text-paper"
      >
        {cause.rank}
      </span>
      <div className="min-w-0 flex-1">
        <h3 className="text-balance font-display text-2xl font-bold leading-tight [font-stretch:110%]">{cause.title}</h3>
        <p className={`num mt-3 font-mono text-3xl font-medium ${loss ? "text-accent" : ""}`}>
          {loss ? "−" : "+"}
          {formatNaira(cause.impact_ngn)}
        </p>
        <p className="mt-1 text-muted">
          <span className="num">{formatPct(cause.share_of_change_pct)}</span> of the change. Without it, profit would
          have been <span className="num font-semibold text-ink">{formatNaira(cause.counterfactual_ngn)}</span>.
        </p>

        <ul className="mt-4 flex flex-wrap items-center gap-2">
          <li>
            <Stamp label={verified ? "Verified" : "Check failed"} tone={verified ? "ink" : "accent"} rotate={-4} />
          </li>
          <li className={pill}>{originLabel[cause.origin]}</li>
          <li className={pill}>{natureLabel[cause.nature]}</li>
          <li className={`${pill} num`}>Confidence {Math.round(cause.confidence * 100)}%</li>
          {cause.retries ? <li className={pill}>Re-tested {cause.retries}x</li> : null}
        </ul>

        <details className="group mt-5" open={defaultOpen}>
          <summary className="inline-flex h-10 cursor-pointer list-none items-center gap-2 rounded-full border-2 border-ink px-4 text-sm font-bold hover:bg-ink hover:text-paper [&::-webkit-details-marker]:hidden">
            Records and checks
            <AltArrowDownIcon size={16} className="transition-transform duration-300 group-open:rotate-180" aria-hidden />
          </summary>

          <div className="mt-4 flex flex-col gap-6 rounded-2xl border-2 border-dashed border-ink/40 bg-paper-2 p-4 sm:p-5">
            {cause.evidence.map((item) => (
              <div key={item.evidence_id}>
                <p className="font-semibold">{item.summary}</p>
                <p className="mt-1 text-sm text-muted">
                  Table <code className="font-mono text-ink">{item.table}</code>. Records{" "}
                  <span className="break-words font-mono text-ink">{item.row_ids.join(", ")}</span>.
                </p>
                <pre className="mt-3 overflow-x-auto rounded-xl bg-ink p-4 font-mono text-[13px] leading-relaxed text-paper">
                  {item.sql}
                </pre>
                {item.check && (
                  <p className="mt-3 flex items-start gap-2 text-sm">
                    {item.check.match ? (
                      <CheckCircleIcon size={18} className="mt-0.5 shrink-0" aria-hidden />
                    ) : (
                      <CloseCircleIcon size={18} className="mt-0.5 shrink-0 text-accent" aria-hidden />
                    )}
                    <span>
                      <span className="font-bold">{item.check.match ? "Checker: matched." : "Checker: did not match."}</span>{" "}
                      <span className="text-muted">
                        {item.check.note ? `${item.check.note[0].toUpperCase()}${item.check.note.slice(1)}. ` : ""}Checked by{" "}
                        {checkedBy(item.check)}.
                      </span>
                    </span>
                  </p>
                )}
              </div>
            ))}

            <div>
              <h4 className="font-mono text-xs font-medium uppercase tracking-[0.16em]">What would prove it wrong</h4>
              <ul className="mt-3 flex flex-col gap-2">
                {cause.falsified_by.map((t) => (
                  <li key={t.test} className="flex items-start gap-2 text-sm">
                    {t.survived ? (
                      <CheckCircleIcon size={18} className="mt-0.5 shrink-0" aria-hidden />
                    ) : (
                      <CloseCircleIcon size={18} className="mt-0.5 shrink-0 text-accent" aria-hidden />
                    )}
                    <span>
                      {t.test}.{" "}
                      <span className="font-bold">{t.survived ? "The cause survived this test." : "The cause did not survive this test."}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <p className="text-sm text-muted">Read from: {cause.depends_on_sources.map((s) => sourceLabel[s]).join(", ")}.</p>
          </div>
        </details>
      </div>
    </article>
  );
}
