"use client";

import type { Investigation } from "@/lib/investigation";
import { formatNaira } from "@/lib/format";
import { Stamp } from "./stamp";
import { AltArrowDownIcon } from "@solar-icons/react/outline";

export function RuledOut({ items }: { items: Investigation["ruled_out"] }) {
  if (items.length === 0) return null;

  return (
    <article className="rounded-2xl border border-rule bg-paper p-5 sm:p-6">
      <div className="flex items-start gap-4">
        <span
          aria-label="Ruled out"
          className="flex size-9 shrink-0 items-center justify-center rounded-full border-2 border-ink font-mono text-sm font-bold text-ink"
        >
          ✓
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex items-baseline justify-between gap-2">
            <h3 className="font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%]">
              What we checked and ruled out
            </h3>
            <Stamp label="Ruled out" tone="accent" rotate={2} />
          </div>

          <p className="mt-2 text-sm text-muted">
            These potential causes were investigated against your data and eliminated, so you do not chase the wrong
            fix:
          </p>

          <ul className="mt-4 flex flex-col gap-3">
            {items.map((item) => (
              <li
                key={item.cause_id}
                className="rounded-xl border border-rule bg-paper-2/40 p-3"
              >
                <p className="font-semibold text-ink line-through decoration-accent decoration-2">
                  {item.hypothesis}
                </p>
                <p className="mt-1 text-xs text-muted leading-relaxed">{item.reason}</p>

                <details className="group mt-2">
                  <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-[11px] font-mono text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
                    <span>Technical detail</span>
                    <AltArrowDownIcon
                      size={12}
                      className="transition-transform duration-200 group-open:rotate-180"
                      aria-hidden
                    />
                  </summary>
                  <div className="mt-1 font-mono text-[11px] text-muted">
                    {item.tested_value_ngn != null && (
                      <p>Tested value: {formatNaira(item.tested_value_ngn)}</p>
                    )}
                    {item.evidence_id && <p>Evidence ID: {item.evidence_id}</p>}
                  </div>
                </details>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}
