import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct } from "@/lib/format";

export function Convergence({ convergence, notTested }: { convergence: Investigation["convergence"]; notTested: string[] }) {
  const explained = Math.min(100, Math.max(0, convergence.explained_pct));
  return (
    <section aria-labelledby="explained" className="border-t border-rule-strong pt-8">
      <h2 id="explained" className="text-xl font-semibold">How much is explained</h2>
      <p className="mt-2 max-w-prose text-lg">
        The causes above explain <strong className="num">{formatNaira(convergence.explained_ngn)}</strong> of the change
        (<span className="num">{formatPct(convergence.explained_pct)}</span>).{" "}
        <strong className="num">{formatNaira(convergence.unexplained_ngn)}</strong> is not explained.
      </p>
      <div className="mt-4 flex h-3 w-full overflow-hidden rounded-full bg-rule" aria-hidden>
        <div className="h-full bg-ink" style={{ width: `${explained}%` }} />
      </div>
      <p className="mt-2 flex justify-between text-sm text-muted">
        <span>Explained</span>
        <span>Not explained</span>
      </p>
      {notTested.length > 0 && (
        <div className="mt-6">
          <h3 className="font-semibold">Not tested in this run</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
            {notTested.map((line) => <li key={line}>{line}</li>)}
          </ul>
        </div>
      )}
    </section>
  );
}
