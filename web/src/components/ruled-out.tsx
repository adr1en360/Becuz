import type { Investigation } from "@/lib/investigation";
import { formatNaira } from "@/lib/format";
import { SectionTitle } from "./receipt";
import { Stamp } from "./stamp";

export function RuledOut({ items }: { items: Investigation["ruled_out"] }) {
  return (
    <section aria-labelledby="ruled-out">
      <SectionTitle id="ruled-out">Ruled out</SectionTitle>
      {items.length === 0 ? (
        <p className="mt-4 text-muted">Nothing was tested and rejected in this run.</p>
      ) : (
        <ul className="mt-6 flex flex-col gap-6">
          {items.map((item, i) => (
            <li key={item.cause_id} className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="font-semibold line-through decoration-accent decoration-2">{item.hypothesis}</p>
                <p className="mt-1 text-sm text-muted">{item.reason}</p>
                {item.tested_value_ngn != null && (
                  <p className="num mt-1 font-mono text-xs text-muted">effect found: {formatNaira(item.tested_value_ngn)}</p>
                )}
              </div>
              <Stamp label="Ruled out" tone="accent" rotate={i % 2 ? 3 : -4} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
