import type { Investigation } from "@/lib/investigation";
import { formatNaira } from "@/lib/format";

export function RuledOut({ items }: { items: Investigation["ruled_out"] }) {
  return (
    <section aria-labelledby="ruled-out" className="border-t border-rule-strong pt-8">
      <h2 id="ruled-out" className="text-xl font-semibold">What was ruled out</h2>
      {items.length === 0 ? (
        <p className="mt-2 text-muted">Nothing was tested and rejected in this run.</p>
      ) : (
        <ul className="mt-4 divide-y divide-rule">
          {items.map((item) => (
            <li key={item.cause_id} className="py-4">
              <p className="font-semibold">{item.hypothesis}</p>
              <p className="mt-1 text-muted">{item.reason}</p>
              {item.tested_value_ngn != null && (
                <p className="num mt-1 text-sm text-muted">Effect found when tested: {formatNaira(item.tested_value_ngn)}.</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
