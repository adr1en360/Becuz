import type { Investigation } from "@/lib/investigation";

export function NextSteps({ data }: { data: Investigation }) {
  const title = new Map(data.causes.map((c) => [c.cause_id, c.title]));
  return (
    <section aria-labelledby="next" className="border-t border-rule-strong pt-8">
      <h2 id="next" className="text-xl font-semibold">What to do this week</h2>
      <ul className="mt-4 divide-y divide-rule">
        {data.summary.what_to_do.map((step) => (
          <li key={step.action} className="py-4">
            <p className="font-semibold">{step.action}</p>
            <p className="mt-1 text-sm text-muted">Because: {title.get(step.cause_id) ?? step.cause_id}</p>
          </li>
        ))}
      </ul>
      {data.owner_questions.length > 0 && (
        <div className="mt-8">
          <h3 className="font-semibold">Questions only you can answer</h3>
          <ul className="mt-2 list-disc space-y-2 pl-5">
            {data.owner_questions.map((q) => <li key={q.question}>{q.question}</li>)}
          </ul>
          <p className="mt-3 text-sm text-muted">Becuz points to the records. What happened to them is for you to decide.</p>
        </div>
      )}
    </section>
  );
}
