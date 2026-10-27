"use client";

import { AltArrowDownIcon, CheckCircleIcon, CloseCircleIcon } from "@solar-icons/react/outline";
import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct, formatSigned } from "@/lib/format";
import { natureLabel, originLabel, sourceLabel } from "@/lib/labels";
import { ConfirmButton } from "./confirm-button";
import { SourceChips } from "./source-chips";
import { Stamp } from "./stamp";

type Cause = Investigation["causes"][number];

export const pill = "rounded-full border border-ink/40 px-3 py-1 font-mono text-xs text-ink";

export const confidenceLabel = (value: number | null | undefined) =>
  typeof value === "number" ? `Confidence ${Math.round(value * 100)}%` : "Not rated";

function checkedBy(check: NonNullable<Cause["evidence"][number]["check"]>) {
  if (check.model) {
    const route = check.via === "nightshift" ? " through Nightshift" : "";
    return `${check.model}${route}${check.signed ? ", signed receipt" : ""}`;
  }
  return check.via === "rules" || check.via === "sample-rules" ? "fixed rules (sample mode)" : check.via;
}

export function CauseBlock({
  cause,
  runId,
  stepNumber,
}: {
  cause: Cause;
  runId: string;
  stepNumber: number;
}) {
  const loss = cause.impact_ngn < 0;
  const verified = cause.evidence.every((e) => e.check?.match);

  return (
    <article className="rounded-2xl border border-rule bg-paper p-5 sm:p-6 transition-all">
      <div className="flex items-start gap-4">
        <span
          aria-label={`Step ${stepNumber}`}
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-sm font-bold text-paper"
        >
          {stepNumber}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%]">
              {cause.title}
            </h3>
            <p className={`num font-mono text-2xl font-bold ${loss ? "text-accent" : "text-ink"}`}>
              {formatSigned(cause.impact_ngn)}
            </p>
          </div>

          <p className="mt-1 text-sm text-muted">
            <span className="num font-semibold text-ink">{formatPct(cause.share_of_change_pct)}</span> of the profit
            change. Without this cause, profit would have been{" "}
            <span className="num font-semibold text-ink">{formatNaira(cause.counterfactual_ngn)}</span>.
          </p>

          {/* Two tags from report: origin and nature */}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Stamp label={verified ? "Verified" : "Check failed"} tone={verified ? "ink" : "accent"} rotate={-2} />
            <span className={`${pill} bg-paper-2`}>{originLabel[cause.origin]}</span>
            <span className={`${pill} bg-paper-2`}>{natureLabel[cause.nature]}</span>
            {cause.retries ? <span className={pill}>Re-tested {cause.retries}x</span> : null}
          </div>

          {/* Source chips */}
          <div className="mt-4">
            <SourceChips evidence={cause.evidence} />
          </div>

          {/* Confirmation button */}
          <div className="mt-4">
            <ConfirmButton runId={runId} causeId={cause.cause_id} />
          </div>

          {/* Collapsible Technical Details */}
          <details className="group mt-5 border-t border-rule/60 pt-3">
            <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
              <span>Technical details</span>
              <AltArrowDownIcon
                size={14}
                className="transition-transform duration-200 group-open:rotate-180"
                aria-hidden
              />
            </summary>

            <div className="mt-3 flex flex-col gap-3 rounded-xl bg-paper-2 p-4 text-xs font-mono text-muted">
              <div>
                <span className="font-semibold text-ink">Checker verification:</span>
                {cause.evidence.map((item) => (
                  <div key={item.evidence_id} className="mt-1">
                    <p className="text-ink">
                      {item.check?.match ? "✓ Match" : "✗ Mismatch"}: {item.check?.note ?? "Independent SQL re-run"}
                    </p>
                    {item.check && (
                      <p className="text-[11px] text-muted">Checked by: {checkedBy(item.check)}</p>
                    )}
                  </div>
                ))}
              </div>

              <div>
                <span className="font-semibold text-ink">Model & Rating: </span>
                <span>{confidenceLabel(cause.confidence)}</span>
              </div>

              <div>
                <span className="font-semibold text-ink">Sources read: </span>
                <span>{cause.depends_on_sources.map((s) => sourceLabel[s]).join(", ")}</span>
              </div>

              {cause.falsified_by.length > 0 && (
                <div>
                  <span className="font-semibold text-ink">Falsification checks:</span>
                  <ul className="mt-1 flex flex-col gap-1">
                    {cause.falsified_by.map((f) => (
                      <li key={f.test} className="flex items-start gap-1.5 text-[11px]">
                        {f.survived ? (
                          <CheckCircleIcon size={14} className="mt-0.5 text-ink shrink-0" aria-hidden />
                        ) : (
                          <CloseCircleIcon size={14} className="mt-0.5 text-accent shrink-0" aria-hidden />
                        )}
                        <span>
                          {f.test} ({f.survived ? "survived" : "failed"})
                        </span>
                      </li>
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
