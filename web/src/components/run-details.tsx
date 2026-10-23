import type { Investigation } from "@/lib/investigation";
import { Barcode } from "./barcode";
import { Leader, SectionTitle } from "./receipt";

export function RunDetails({ data }: { data: Investigation }) {
  const { stats } = data;
  const models = Object.entries(stats.models);
  return (
    <section aria-labelledby="details">
      <SectionTitle id="details">How this was run</SectionTitle>
      <div className="mt-6 flex flex-col gap-2 text-sm">
        <Leader label="Mode" value={data.mode} />
        <Leader label="Data" value={`${data.synthetic ? "Synthetic" : "Real"}${data.scenario ? `, ${data.scenario}` : ""}`} />
        <Leader label="Duration" value={`${stats.duration_s.toFixed(1)} s`} />
        <Leader label="Zetaris queries" value={stats.zetaris_queries} />
        <Leader label="Model calls" value={stats.model_calls} />
        <Leader label="Models" value={models.length ? models.map(([m, n]) => `${m} (${n})`).join(", ") : "none used"} />
      </div>
      <p className="mt-4 break-all font-mono text-xs text-muted">Trace file: {data.trace_file}</p>
      <p className="mt-1 text-xs text-muted">The step-by-step trace will show here once the server serves it.</p>

      <h3 className="mt-8 font-mono text-xs font-medium uppercase tracking-[0.16em]">Keep in mind</h3>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
        {data.limitations.map((line) => <li key={line}>{line}</li>)}
      </ul>

      <div className="mt-10 flex flex-col items-center gap-2">
        <Barcode seed={data.run_id} />
        <p className="font-mono text-xs tracking-[0.2em] text-muted">{data.run_id}</p>
      </div>
    </section>
  );
}
