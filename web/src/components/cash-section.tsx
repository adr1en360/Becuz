import { AltArrowDownIcon } from "@solar-icons/react/bold";
import type { Investigation } from "@/lib/investigation";
import { formatNaira } from "@/lib/format";
import { confidenceLabel, detailsButton, pill } from "./cause-block";
import { ConfirmButton } from "./confirm-button";
import { EvidencePanel } from "./evidence-panel";
import { SectionTitle } from "./receipt";
import { Stamp } from "./stamp";

type Props = { runId: string; gaps: NonNullable<Investigation["cash_gaps"]>; lines: string[]; questions: Investigation["owner_questions"] };

export function CashSection({ runId, gaps, lines, questions }: Props) {
  return (
    <section aria-labelledby="cash">
      <SectionTitle id="cash">Money missing from your account</SectionTitle>
      <p className="mt-3 text-muted">This is cash, not a profit loss. The sales still count in your profit.</p>
      {lines.map((line) => (
        <p key={line} className="mt-4 max-w-prose text-lg">{line}</p>
      ))}

      <div className="mt-8 flex flex-col gap-10">
        {gaps.map((gap, i) => {
          const verified = gap.evidence.every((e) => e.check?.match);
          return (
            <article key={gap.cause_id}>
              <h3 className="text-balance font-display text-2xl font-bold leading-tight [font-stretch:110%]">{gap.title}</h3>
              <p className="num mt-3 font-mono text-3xl font-medium text-accent">{formatNaira(gap.impact_ngn)} missing</p>
              <ul className="mt-4 flex flex-wrap items-center gap-2">
                <li>
                  <Stamp label={verified ? "Verified" : "Check failed"} tone={verified ? "ink" : "accent"} rotate={3} />
                </li>
                <li className={`${pill} num`}>{confidenceLabel(gap.confidence)}</li>
                {gap.retries ? <li className={pill}>Re-tested {gap.retries}x</li> : null}
              </ul>
              <details className="group mt-5" open={i === 0}>
                <summary className={detailsButton}>
                  Records and checks
                  <AltArrowDownIcon size={16} className="transition-transform duration-300 group-open:rotate-180" aria-hidden />
                </summary>
                <EvidencePanel evidence={gap.evidence} falsifiedBy={gap.falsified_by} sources={gap.depends_on_sources} />
              </details>
              <ConfirmButton runId={runId} causeId={gap.cause_id} />
            </article>
          );
        })}
      </div>

      {questions.length > 0 && (
        <div className="mt-8 rounded-2xl border-2 border-dashed border-ink/40 bg-paper-2 p-4 sm:p-5">
          <h3 className="font-mono text-xs font-medium uppercase tracking-[0.16em]">Questions only you can answer</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5">
            {questions.map((q) => <li key={q.question}>{q.question}</li>)}
          </ul>
          <p className="mt-3 text-sm text-muted">Becuz points to the records. What happened to them is for you to decide.</p>
        </div>
      )}
    </section>
  );
}
