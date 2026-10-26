import type { TraceEvent } from "@/lib/api";
import { Receipt, SectionTitle } from "./receipt";
import { TraceList } from "./trace-list";

export function LiveTrace({ events }: { events: TraceEvent[] }) {
  return (
    <Receipt>
      <SectionTitle id="live-heading">Working on it</SectionTitle>
      <div className="mt-6" role="log" aria-live="polite" aria-labelledby="live-heading">
        {events.length === 0 ? (
          <p className="line-busy text-sm text-muted">Starting the run. The first step shows here in a moment.</p>
        ) : (
          <TraceList events={events} busy />
        )}
      </div>
      <p className="mt-8 font-mono text-xs uppercase tracking-[0.16em] text-muted">Printing your receipt...</p>
    </Receipt>
  );
}
