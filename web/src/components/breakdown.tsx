"use client";

import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatPct, formatSigned } from "@/lib/format";
import { componentLabel, treeStatusLabel } from "@/lib/labels";
import { useSeen } from "@/lib/use-seen";
import { Leader, SectionTitle } from "./receipt";

function Row({ node }: { node: Investigation["tree"][number] }) {
  const [ref, seen] = useSeen<HTMLLIElement>();
  const loss = node.profit_effect_ngn < 0;
  return (
    <li ref={ref}>
      <Leader label={componentLabel[node.component]} value={formatSigned(node.profit_effect_ngn)} valueClass={loss ? "text-accent" : ""} />
      <div className="mt-2 h-2 w-full rounded-full bg-rule" aria-hidden>
        <div
          data-seen={seen}
          className={`draw h-full rounded-full ${loss ? "bg-accent" : "bg-ink"}`}
          style={{ width: `${Math.min(100, Math.abs(node.share_of_change_pct))}%` }}
        />
      </div>
      <p className="num mt-2 font-mono text-xs leading-relaxed text-muted">
        avg {formatNaira(node.baseline_ngn)} to {formatNaira(node.current_ngn)}
        {node.share_of_change_pct !== 0 &&
          (node.share_of_change_pct < 0
            ? ` / offset by ${formatPct(Math.abs(node.share_of_change_pct))}`
            : ` / ${formatPct(node.share_of_change_pct)} of the change`)}
        {" / "}
        {treeStatusLabel[node.status].toLowerCase()}
      </p>
    </li>
  );
}

export function Breakdown({ tree }: { tree: Investigation["tree"] }) {
  return (
    <section aria-labelledby="breakdown">
      <SectionTitle id="breakdown">Where it went</SectionTitle>
      <ul className="mt-6 flex flex-col gap-6">
        {tree.map((node) => <Row key={node.component} node={node} />)}
      </ul>
    </section>
  );
}
