"use client";

import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct, formatSigned } from "@/lib/format";
import { componentLabel, treeStatusLabel } from "@/lib/labels";
import { useSeen } from "@/lib/use-seen";
import { Leader } from "./receipt";
import { AltArrowDownIcon } from "@solar-icons/react/outline";

function Row({ node }: { node: Investigation["tree"][number] }) {
  const [ref, seen] = useSeen<HTMLLIElement>();
  const loss = node.profit_effect_ngn < 0;
  return (
    <li ref={ref} className="flex flex-col gap-1">
      <Leader
        label={componentLabel[node.component]}
        value={formatSigned(node.profit_effect_ngn)}
        valueClass={loss ? "text-accent font-bold" : "text-ink font-bold"}
      />
      <div className="mt-1 h-2 w-full rounded-full bg-rule" aria-hidden>
        <div
          data-seen={seen}
          className={`draw h-full rounded-full ${loss ? "bg-accent" : "bg-ink"}`}
          style={{ width: `${Math.min(100, Math.abs(node.share_of_change_pct))}%` }}
        />
      </div>
      <p className="num mt-1 font-mono text-xs leading-relaxed text-muted">
        avg {formatNaira(node.baseline_ngn)} → {formatNaira(node.current_ngn)}
        {node.share_of_change_pct !== 0 &&
          (node.share_of_change_pct < 0
            ? ` · offset by ${formatPct(Math.abs(node.share_of_change_pct))}`
            : ` · ${formatPct(node.share_of_change_pct)} of change`)}
        {" · "}
        {treeStatusLabel[node.status].toLowerCase()}
      </p>
    </li>
  );
}

export function Breakdown({ tree }: { tree: Investigation["tree"] }) {
  return (
    <article className="rounded-2xl border border-rule bg-paper p-5 sm:p-6">
      <div className="flex items-start gap-4">
        <span
          aria-label="Step 2"
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-sm font-bold text-paper"
        >
          2
        </span>

        <div className="min-w-0 flex-1">
          <h3 className="font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%]">
            Where the money went
          </h3>

          <p className="mt-2 text-sm leading-relaxed text-muted">
            Profit = sales − cost of goods − wastage − running costs. Here is how each component moved this week.
          </p>

          <ul className="mt-5 flex flex-col gap-4">
            {tree.map((node) => (
              <Row key={node.component} node={node} />
            ))}
          </ul>

          <details className="group mt-5 border-t border-rule/60 pt-3">
            <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
              <span>Technical details</span>
              <AltArrowDownIcon
                size={14}
                className="transition-transform duration-200 group-open:rotate-180"
                aria-hidden
              />
            </summary>
            <div className="mt-2 rounded-xl bg-paper-2 p-3 font-mono text-xs text-muted">
              <p className="text-ink font-semibold">Data source: Zetaris USL table becuz.daily_pnl</p>
              <p className="mt-1">
                Computes the full profit tree per day directly in Zetaris. Every agent reads this unified semantic
                layer; no raw CSV math is performed in client prompts.
              </p>
            </div>
          </details>
        </div>
      </div>
    </article>
  );
}
