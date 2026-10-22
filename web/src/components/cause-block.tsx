import { AltArrowDownIcon, CheckCircleIcon, CloseCircleIcon } from "@solar-icons/react/bold";
import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct } from "@/lib/format";
import { natureLabel, originLabel, sourceLabel } from "@/lib/labels";

type Cause = Investigation["causes"][number];

const pill = "rounded-full border border-rule-strong px-3 py-1 text-sm text-muted";

function checkedBy(check: NonNullable<Cause["evidence"][number]["check"]>) {
  const who = check.model ?? (check.via === "rules" || check.via === "sample-rules" ? "fixed rules" : check.via);
  return `${who}${check.signed ? ", signed" : ""}`;
}

export function CauseBlock({ cause, defaultOpen = false }: { cause: Cause; defaultOpen?: boolean }) {
  const loss = cause.impact_ngn < 0;
  return (
    <article>
      <h3 className="text-balance text-xl font-semibold leading-snug">{cause.title}</h3>
      <p className="mt-2 text-lg">
        This {loss ? "cut" : "added to"} profit by{" "}
        <strong className={`num ${loss ? "text-accent" : ""}`}>{formatNaira(cause.impact_ngn)}</strong>,{" "}
        <span className="num">{formatPct(cause.share_of_change_pct)}</span> of the change. Without it, profit would
        have been <span className="num font-semibold">{formatNaira(cause.counterfactual_ngn)}</span>.
      </p>
      <ul className="mt-3 flex flex-wrap gap-2">
        <li className={pill}>{originLabel[cause.origin]}</li>
        <li className={pill}>{natureLabel[cause.nature]}</li>
        <li className={`${pill} num`}>Confidence {Math.round(cause.confidence * 100)}%</li>
        {cause.retries ? <li className={pill}>Re-tested {cause.retries}x</li> : null}
      </ul>

      <details className="group mt-4" open={defaultOpen}>
        <summary className="inline-flex h-10 cursor-pointer list-none items-center gap-2 rounded-full border border-ink px-4 text-sm font-semibold hover:bg-ink hover:text-paper [&::-webkit-details-marker]:hidden">
          Records and checks
          <AltArrowDownIcon size={16} className="transition-transform group-open:rotate-180" aria-hidden />
        </summary>

        <div className="mt-5 flex flex-col gap-6 border-l border-rule-strong pl-5">
          {cause.evidence.map((item) => (
            <div key={item.evidence_id}>
              <p className="font-medium">{item.summary}</p>
              <p className="mt-1 text-sm text-muted">
                Table <code className="font-mono text-ink">{item.table}</code>. Records{" "}
                <span className="font-mono text-ink">{item.row_ids.join(", ")}</span>.
              </p>
              <pre className="mt-3 overflow-x-auto rounded-xl border border-rule bg-field p-4 font-mono text-sm leading-relaxed">
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
                    <span className="font-semibold">{item.check.match ? "Checker: matched." : "Checker: did not match."}</span>{" "}
                    <span className="text-muted">
                      {item.check.note ? `${item.check.note[0].toUpperCase()}${item.check.note.slice(1)}. ` : ""}Checked by {checkedBy(item.check)}.
                    </span>
                  </span>
                </p>
              )}
            </div>
          ))}

          <div>
            <h4 className="font-semibold">What would prove it wrong</h4>
            <ul className="mt-2 flex flex-col gap-2">
              {cause.falsified_by.map((t) => (
                <li key={t.test} className="flex items-start gap-2 text-sm">
                  {t.survived ? (
                    <CheckCircleIcon size={18} className="mt-0.5 shrink-0" aria-hidden />
                  ) : (
                    <CloseCircleIcon size={18} className="mt-0.5 shrink-0 text-accent" aria-hidden />
                  )}
                  <span>
                    {t.test}. <span className="font-semibold">{t.survived ? "The cause survived this test." : "The cause did not survive this test."}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-sm text-muted">
            Read from: {cause.depends_on_sources.map((s) => sourceLabel[s]).join(", ")}.
          </p>
        </div>
      </details>
    </article>
  );
}
