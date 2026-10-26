import { AltArrowDownIcon } from "@solar-icons/react/bold";
import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct } from "@/lib/format";
import { natureLabel, originLabel } from "@/lib/labels";
import { ConfirmButton } from "./confirm-button";
import { EvidencePanel } from "./evidence-panel";
import { Stamp } from "./stamp";

type Cause = Investigation["causes"][number];

export const pill = "rounded-full border border-ink/40 px-3 py-1 font-mono text-xs text-ink";

export const confidenceLabel = (value: number | null | undefined) =>
  typeof value === "number" ? `Confidence ${Math.round(value * 100)}%` : "Not rated";

export const detailsButton =
  "inline-flex h-10 cursor-pointer list-none items-center gap-2 rounded-full border-2 border-ink px-4 text-sm font-bold hover:bg-ink hover:text-paper [&::-webkit-details-marker]:hidden";

export function CauseBlock({ cause, runId, defaultOpen = false }: { cause: Cause; runId: string; defaultOpen?: boolean }) {
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
          <li className={`${pill} num`}>{confidenceLabel(cause.confidence)}</li>
          {cause.retries ? <li className={pill}>Re-tested {cause.retries}x</li> : null}
        </ul>

        <details className="group mt-5" open={defaultOpen}>
          <summary className={detailsButton}>
            Records and checks
            <AltArrowDownIcon size={16} className="transition-transform duration-300 group-open:rotate-180" aria-hidden />
          </summary>
          <EvidencePanel evidence={cause.evidence} falsifiedBy={cause.falsified_by} sources={cause.depends_on_sources} />
        </details>
        <ConfirmButton runId={runId} causeId={cause.cause_id} />
      </div>
    </article>
  );
}
