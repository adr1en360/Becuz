import type { Investigation } from "@/lib/investigation";
import { CauseBlock } from "./cause-block";
import { SectionTitle } from "./receipt";

export function CauseList({ causes }: { causes: Investigation["causes"] }) {
  const ranked = [...causes].sort((a, b) => a.rank - b.rank);
  return (
    <section aria-labelledby="causes">
      <SectionTitle id="causes">Causes</SectionTitle>
      <p className="mt-3 text-muted">
        {causes.length} supported {causes.length === 1 ? "cause" : "causes"}
        {causes.length > 0 && ", largest first. Each one opens to its records"}.
      </p>
      {causes.length === 0 && (
        <p className="mt-6 max-w-prose text-lg">No cause passed the checks this week, so Becuz does not name one.</p>
      )}
      <div className="mt-8 flex flex-col gap-12">
        {ranked.map((cause, i) => <CauseBlock key={cause.cause_id} cause={cause} defaultOpen={i === 0} />)}
      </div>
    </section>
  );
}
