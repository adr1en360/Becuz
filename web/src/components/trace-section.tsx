import type { TraceEvent } from "@/lib/api";
import { SectionTitle } from "./receipt";
import { TraceList } from "./trace-list";

export function TraceSection({ events, traceFile }: { events: TraceEvent[]; traceFile: string }) {
  const rejected = events.filter((e) => e.action === "rejected").length;
  return (
    <section aria-labelledby="trace">
      <SectionTitle id="trace">How I got here</SectionTitle>
      <p className="mt-3 text-muted">
        Every step the agents took, in order, with the engine or model behind it.
        {rejected > 0 && ` The Checker turned down ${rejected} ${rejected === 1 ? "claim" : "claims"} on the way.`}
      </p>
      <details className="group mt-5">
        <summary className="inline-flex h-10 cursor-pointer list-none items-center rounded-full border-2 border-ink px-4 text-sm font-bold hover:bg-ink hover:text-paper [&::-webkit-details-marker]:hidden">
          <span className="group-open:hidden">Show {events.length} steps</span>
          <span className="hidden group-open:inline">Hide steps</span>
        </summary>
        <div className="mt-6">
          <TraceList events={events} />
        </div>
      </details>
      <p className="mt-6 break-all font-mono text-xs text-muted">Trace file: {traceFile}</p>
    </section>
  );
}
