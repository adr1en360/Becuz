import { CheckCircleIcon, CloseCircleIcon, QuestionCircleIcon } from "@solar-icons/react/bold";
import type { Investigation } from "@/lib/investigation";
import { formatPct } from "@/lib/format";

type Entry = NonNullable<Investigation["memory"]>[number];

function Held({ held }: { held: Entry["held_again"] }) {
  if (held === true) return <><CheckCircleIcon size={18} aria-hidden /> Held again this week</>;
  if (held === false) return <><CloseCircleIcon size={18} className="text-accent" aria-hidden /> Did not hold this week</>;
  return <><QuestionCircleIcon size={18} aria-hidden /> Not tested this week</>;
}

export function MemoryNote({ entries }: { entries: NonNullable<Investigation["memory"]> }) {
  return (
    <section aria-labelledby="memory" className="mt-8 rounded-2xl border-2 border-dashed border-ink/40 bg-paper-2 p-4 sm:p-5">
      <h2 id="memory" className="font-mono text-xs font-medium uppercase tracking-[0.16em]">
        What Becuz remembered from you
      </h2>
      <ul className="mt-3 flex flex-col gap-4">
        {entries.map((entry) => (
          <li key={`${entry.cause_id}-${entry.confirmed_at}`}>
            <p className="text-lg">{entry.message}</p>
            <p className="mt-1 flex items-center gap-2 text-sm text-muted">
              <Held held={entry.held_again} />
              {typeof entry.confidence_before === "number" && typeof entry.confidence_after === "number" && (
                <span className="num font-mono text-xs">
                  / confidence {formatPct(entry.confidence_before * 100)} to {formatPct(entry.confidence_after * 100)}
                </span>
              )}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
