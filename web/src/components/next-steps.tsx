import { CheckSquareIcon, ScissorsIcon } from "@solar-icons/react/outline";
import type { Investigation } from "@/lib/investigation";
import { SectionTitle } from "./receipt";

export function NextSteps({ data, questions }: { data: Investigation; questions: Investigation["owner_questions"] }) {
  const title = new Map(data.causes.map((c) => [c.cause_id, c.title]));
  return (
    <section aria-labelledby="next">
      <div className="mb-6 flex items-center gap-3 text-muted" aria-hidden>
        <ScissorsIcon size={20} />
        <span className="cut-line flex-1" />
        <span className="font-mono text-xs uppercase tracking-[0.16em]">Tear off and keep</span>
      </div>
      <SectionTitle id="next">What to do this week</SectionTitle>
      {data.summary.what_to_do.length === 0 && (
        <p className="mt-4 text-muted">This run found nothing to change. If the drop continues next week, ask again.</p>
      )}
      <ul className="mt-6 flex flex-col gap-5">
        {data.summary.what_to_do.map((step) => (
          <li key={step.action} className="flex items-start gap-3">
            <CheckSquareIcon size={22} className="mt-0.5 shrink-0" aria-hidden />
            <div>
              <p className="font-semibold">{step.action}</p>
              <p className="mt-1 text-sm text-muted">Because: {title.get(step.cause_id) ?? step.cause_id}</p>
            </div>
          </li>
        ))}
      </ul>
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
