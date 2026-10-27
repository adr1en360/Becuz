import type { Investigation } from "@/lib/investigation";
import { CauseBlock } from "./cause-block";
import { SectionTitle } from "./receipt";

export function CauseList({
  causes,
  runId,
  startStep = 3,
}: {
  causes: Investigation["causes"];
  runId: string;
  startStep?: number;
}) {
  const ranked = [...causes].sort((a, b) => a.rank - b.rank);

  return (
    <section aria-labelledby="causes" className="flex flex-col gap-4">
      <SectionTitle id="causes">Causes</SectionTitle>
      <p className="text-sm text-muted">
        {causes.length} supported {causes.length === 1 ? "cause" : "causes"}
        {causes.length > 0 ? ", largest first. Each claim is backed by records and independently verified." : "."}
      </p>

      {causes.length === 0 ? (
        <div className="rounded-2xl border border-rule bg-paper p-5 text-muted">
          No cause passed the checks in this period, so Becuz does not name one.
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {ranked.map((cause, index) => (
            <CauseBlock
              key={cause.cause_id}
              cause={cause}
              runId={runId}
              stepNumber={startStep + index}
            />
          ))}
        </div>
      )}
    </section>
  );
}
