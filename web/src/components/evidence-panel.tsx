import { CheckCircleIcon, CloseCircleIcon } from "@solar-icons/react/bold";
import type { Investigation } from "@/lib/investigation";
import { sourceLabel } from "@/lib/labels";

type Cause = Investigation["causes"][number];
type Evidence = Cause["evidence"][number];

type Props = {
  evidence: Evidence[];
  falsifiedBy: Cause["falsified_by"];
  sources: Cause["depends_on_sources"];
};

function checkedBy(check: NonNullable<Evidence["check"]>) {
  if (check.model) {
    const route = check.via === "nightshift" ? " through Nightshift" : "";
    return `${check.model}${route}${check.signed ? ", signed receipt" : ""}`;
  }
  return check.via === "rules" || check.via === "sample-rules" ? "fixed rules (sample mode)" : check.via;
}

function sentence(text: string) {
  const trimmed = text.trim();
  return trimmed ? `${trimmed[0].toUpperCase()}${trimmed.slice(1)} ` : "";
}

const Mark = ({ ok }: { ok: boolean }) =>
  ok ? (
    <CheckCircleIcon size={18} className="mt-0.5 shrink-0" aria-hidden />
  ) : (
    <CloseCircleIcon size={18} className="mt-0.5 shrink-0 text-accent" aria-hidden />
  );

export function EvidencePanel({ evidence, falsifiedBy, sources }: Props) {
  return (
    <div className="mt-4 flex flex-col gap-6 rounded-2xl border-2 border-dashed border-ink/40 bg-paper-2 p-4 sm:p-5">
      {evidence.map((item) => (
        <div key={item.evidence_id}>
          <p className="font-semibold">{item.summary}</p>
          <p className="mt-1 text-sm text-muted">
            Table <code className="font-mono text-ink">{item.table}</code>. Records{" "}
            <span className="break-words font-mono text-ink">{item.row_ids.join(", ")}</span>.
          </p>
          <pre className="mt-3 overflow-x-auto rounded-xl bg-ink p-4 font-mono text-[13px] leading-relaxed text-paper">
            {item.sql}
          </pre>
          {item.check && (
            <p className="mt-3 flex items-start gap-2 text-sm">
              <Mark ok={item.check.match} />
              <span>
                <span className="font-bold">{item.check.match ? "Checker: matched." : "Checker: did not match."}</span>{" "}
                <span className="text-muted">
                  {sentence(item.check.note ?? "")}Checked by {checkedBy(item.check)}.
                </span>
              </span>
            </p>
          )}
        </div>
      ))}

      <div>
        <h4 className="font-mono text-xs font-medium uppercase tracking-[0.16em]">What would prove it wrong</h4>
        <ul className="mt-3 flex flex-col gap-2">
          {falsifiedBy.map((t) => (
            <li key={t.test} className="flex items-start gap-2 text-sm">
              <Mark ok={t.survived} />
              <span>
                {t.test}.{" "}
                <span className="font-bold">{t.survived ? "It survived this test." : "It did not survive this test."}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      <p className="text-sm text-muted">Read from: {sources.map((s) => sourceLabel[s]).join(", ")}.</p>
    </div>
  );
}
