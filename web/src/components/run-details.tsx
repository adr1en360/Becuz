import type { Investigation } from "@/lib/investigation";

const row = "flex justify-between gap-6 py-2.5";

export function RunDetails({ data }: { data: Investigation }) {
  const { stats } = data;
  const models = Object.entries(stats.models);
  return (
    <section aria-labelledby="details" className="border-t border-rule-strong pt-8">
      <h2 id="details" className="text-xl font-semibold">How this was run</h2>
      <dl className="num mt-4 divide-y divide-rule text-sm">
        <div className={row}><dt className="text-muted">Mode</dt><dd>{data.mode}</dd></div>
        <div className={row}><dt className="text-muted">Data</dt><dd>{data.synthetic ? "Synthetic" : "Real"}{data.scenario ? `, scenario ${data.scenario}` : ""}</dd></div>
        <div className={row}><dt className="text-muted">Duration</dt><dd>{stats.duration_s.toFixed(1)} s</dd></div>
        <div className={row}><dt className="text-muted">Zetaris queries</dt><dd>{stats.zetaris_queries}</dd></div>
        <div className={row}><dt className="text-muted">Model calls</dt><dd>{stats.model_calls}</dd></div>
        <div className={row}><dt className="text-muted">Models</dt><dd>{models.length ? models.map(([m, n]) => `${m} (${n})`).join(", ") : "None used"}</dd></div>
        <div className={row}><dt className="text-muted">Trace file</dt><dd className="break-all font-mono">{data.trace_file}</dd></div>
      </dl>
      <p className="mt-3 text-sm text-muted">The step-by-step trace will show here once the server serves it.</p>
      <h3 className="mt-8 font-semibold">Keep in mind</h3>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
        {data.limitations.map((line) => <li key={line}>{line}</li>)}
      </ul>
    </section>
  );
}
