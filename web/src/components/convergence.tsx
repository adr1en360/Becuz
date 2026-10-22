import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct } from "@/lib/format";

type Props = { convergence: Investigation["convergence"]; change: number; notTested: string[] };

export function Convergence({ convergence, change, notTested }: Props) {
  const { explained_ngn, explained_pct, unexplained_ngn } = convergence;
  const filled = Math.min(100, Math.max(0, explained_pct));
  const opposite = unexplained_ngn !== 0 && Math.sign(unexplained_ngn) !== Math.sign(change);
  return (
    <section aria-labelledby="explained" className="border-t border-rule-strong pt-8">
      <h2 id="explained" className="text-xl font-semibold">How much is explained</h2>
      <p className="mt-2 max-w-prose text-lg">
        The tested causes explain <strong className="num">{formatNaira(explained_ngn)}</strong> of the{" "}
        <span className="num">{formatNaira(change)}</span> change (<span className="num">{formatPct(explained_pct)}</span>).{" "}
        {unexplained_ngn === 0 ? (
          "Nothing is left unexplained."
        ) : opposite ? (
          <>Something outside these causes pushed profit the other way by <strong className="num">{formatNaira(unexplained_ngn)}</strong>.</>
        ) : (
          <><strong className="num">{formatNaira(unexplained_ngn)}</strong> is not explained.</>
        )}
      </p>
      <div className="mt-4 flex h-3 w-full overflow-hidden rounded-full bg-rule" aria-hidden>
        <div className="h-full bg-ink" style={{ width: `${filled}%` }} />
      </div>
      <p className="mt-2 flex justify-between text-sm text-muted">
        <span>Explained{explained_pct > 100 ? " (over 100%)" : ""}</span>
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
