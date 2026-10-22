import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct, formatSigned } from "@/lib/format";
import { componentLabel, treeStatusLabel } from "@/lib/labels";

export function Breakdown({ tree }: { tree: Investigation["tree"] }) {
  return (
    <section aria-labelledby="breakdown" className="border-t border-rule-strong pt-8">
      <h2 id="breakdown" className="text-xl font-semibold">Where it went</h2>
      <p className="mt-1 text-muted">Each part of your profit, this week against your 4-week average.</p>
      <ul className="mt-5 divide-y divide-rule">
        {tree.map((node) => {
          const loss = node.profit_effect_ngn < 0;
          return (
            <li key={node.component} className="py-4">
              <div className="flex items-baseline justify-between gap-4">
                <span className="font-semibold">{componentLabel[node.component]}</span>
                <span className={`num whitespace-nowrap font-semibold ${loss ? "text-accent" : ""}`}>
                  {formatSigned(node.profit_effect_ngn)}
                  <span className="sr-only"> effect on profit</span>
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full rounded-full bg-rule" aria-hidden>
                <div
                  className={`h-full rounded-full ${loss ? "bg-accent" : "bg-ink"}`}
                  style={{ width: `${Math.min(100, Math.abs(node.share_of_change_pct))}%` }}
                />
              </div>
              <p className="num mt-2 text-sm text-muted">
                Average {formatNaira(node.baseline_ngn)}, this week {formatNaira(node.current_ngn)}.{" "}
                {node.share_of_change_pct !== 0 && <>{formatPct(node.share_of_change_pct)} of the change. </>}
                {treeStatusLabel[node.status]}.
              </p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
