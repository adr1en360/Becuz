"use client";

import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct } from "@/lib/format";
import { useSeen } from "@/lib/use-seen";
import { Leader, SectionTitle } from "./receipt";

type Props = { convergence: Investigation["convergence"]; change: number; notTested: string[] };

export function Convergence({ convergence, change, notTested }: Props) {
  const { explained_ngn, explained_pct, unexplained_ngn } = convergence;
  const [ref, seen] = useSeen<HTMLDivElement>();
  const filled = Math.min(100, Math.max(0, explained_pct));
  const opposite = unexplained_ngn !== 0 && Math.sign(unexplained_ngn) !== Math.sign(change);
  return (
    <section aria-labelledby="explained">
      <SectionTitle id="explained">How much is explained</SectionTitle>
      <div className="mt-6 flex flex-col gap-2">
        <Leader label="Change this week" value={formatNaira(change)} />
        <Leader label="Explained by causes" value={formatNaira(explained_ngn)} />
        <div className="mt-2 border-t-4 border-double border-ink pt-3">
          <Leader
            label={opposite ? "Pulled the other way" : "Not explained"}
            value={formatNaira(unexplained_ngn)}
            valueClass="text-xl"
          />
        </div>
      </div>

      <p className="mt-5 max-w-prose text-lg">
        The tested causes explain <span className="num font-bold">{formatPct(explained_pct)}</span> of the change.{" "}
        {unexplained_ngn === 0
          ? "Nothing is left unexplained."
          : opposite
            ? "Something outside these causes pushed profit the other way."
            : "The rest has no cause the checks could support."}
      </p>
      <div ref={ref} className="mt-4 h-3 w-full rounded-full bg-rule" aria-hidden>
        <div data-seen={seen} className="draw h-full rounded-full bg-ink" style={{ width: `${filled}%` }} />
      </div>
      <p className="mt-2 flex justify-between font-mono text-xs text-muted">
        <span>Explained{explained_pct > 100 ? " (over 100%)" : ""}</span>
        <span>Not explained</span>
      </p>

      {notTested.length > 0 && (
        <div className="mt-6">
          <h3 className="font-mono text-xs font-medium uppercase tracking-[0.16em]">Not tested in this run</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
            {notTested.map((line) => <li key={line}>{line}</li>)}
          </ul>
        </div>
      )}
    </section>
  );
}
