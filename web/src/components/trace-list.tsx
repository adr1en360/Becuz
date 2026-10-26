import type { TraceEvent } from "@/lib/api";
import { causeName, describeAction, engineName, secondsSince } from "@/lib/trace";

const tag = "rounded-full border border-ink/40 px-2 py-0.5 font-mono text-[0.7rem] leading-none";

export function TraceList({ events, busy = false }: { events: TraceEvent[]; busy?: boolean }) {
  return (
    <ol className="flex flex-col gap-5">
      {events.map((e, i) => {
        const rejected = e.action === "rejected";
        const engine = engineName(e);
        const cause = causeName(e);
        return (
          <li key={`${e.timestamp}-${i}`} className="grid grid-cols-[3.25rem_minmax(0,1fr)] gap-3">
            <span className="num pt-0.5 font-mono text-xs text-muted">+{secondsSince(events[0], e)}s</span>
            <div className="min-w-0">
              <p className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className={`font-semibold ${rejected ? "text-accent" : ""}`}>
                  {e.agent_name}: {describeAction(e).toLowerCase()}
                </span>
                {cause && <span className="font-mono text-xs text-muted">{cause}</span>}
              </p>
              <p className="mt-1 text-sm leading-relaxed text-muted">{e.output_summary}</p>
              {(engine || e.model || e.via) && (
                <ul className="mt-2 flex flex-wrap gap-1.5">
                  {engine && <li className={tag}>{engine}</li>}
                  {e.model && <li className={tag}>{e.model}</li>}
                  {e.via && <li className={tag}>via {e.via}</li>}
                </ul>
              )}
            </div>
          </li>
        );
      })}
      {busy && (
        <li className="line-busy grid grid-cols-[3.25rem_minmax(0,1fr)] gap-3" aria-hidden>
          <span className="font-mono text-xs text-muted">...</span>
          <span className="text-sm text-muted">Waiting for the next step</span>
        </li>
      )}
    </ol>
  );
}
