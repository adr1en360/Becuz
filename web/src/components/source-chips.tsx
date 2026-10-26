"use client";

import { useState } from "react";
import type { Investigation } from "@/lib/investigation";
import { tableChipName } from "@/lib/labels";
import { AltArrowDownIcon, DocumentTextIcon } from "@solar-icons/react/outline";

type Evidence = Investigation["causes"][number]["evidence"][number];

export function SourceChips({ evidence }: { evidence: Evidence[] }) {
  const [activeId, setActiveId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted">Sources:</span>
        {evidence.map((item, index) => {
          const tableName = tableChipName(item.table);
          const rowSummary =
            item.row_ids.length === 1 ? item.row_ids[0] : `${item.row_ids.length} records`;
          const chipLabel = `[${index + 1}] ${tableName} · ${rowSummary}`;
          const isSelected = activeId === item.evidence_id;

          return (
            <button
              key={item.evidence_id}
              type="button"
              onClick={() => setActiveId(isSelected ? null : item.evidence_id)}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-mono text-xs transition-colors active:scale-95 ${
                isSelected
                  ? "border-accent bg-accent text-paper font-semibold"
                  : "border-ink/40 bg-paper hover:border-ink hover:text-ink text-muted"
              }`}
            >
              <DocumentTextIcon size={14} aria-hidden />
              <span>{chipLabel}</span>
            </button>
          );
        })}
      </div>

      {/* Expanded citation detail when a chip is tapped */}
      {activeId && (
        <div className="mt-2 rounded-2xl border border-ink/20 bg-paper-2 p-4 text-xs font-mono">
          {evidence
            .filter((e) => e.evidence_id === activeId)
            .map((item) => (
              <div key={item.evidence_id} className="flex flex-col gap-2">
                <div className="flex items-center justify-between border-b border-rule pb-2">
                  <span className="font-sans font-semibold text-sm text-ink">{item.summary}</span>
                  <button
                    type="button"
                    onClick={() => setActiveId(null)}
                    className="text-muted hover:text-ink text-xs underline font-sans"
                  >
                    Close
                  </button>
                </div>

                <div>
                  <span className="text-muted font-sans font-medium">Table: </span>
                  <code className="rounded bg-paper px-1.5 py-0.5 text-ink">{item.table}</code>
                </div>

                <div>
                  <span className="text-muted font-sans font-medium">Record IDs ({item.row_ids.length}): </span>
                  <p className="mt-1 max-h-24 overflow-y-auto rounded bg-paper p-2 font-mono text-ink text-[11px] leading-relaxed break-words">
                    {item.row_ids.join(", ")}
                  </p>
                </div>

                <details className="group mt-1">
                  <summary className="inline-flex cursor-pointer items-center gap-1 font-sans text-xs font-semibold text-accent hover:underline">
                    Show the query
                    <AltArrowDownIcon
                      size={14}
                      className="transition-transform duration-200 group-open:rotate-180"
                      aria-hidden
                    />
                  </summary>
                  <pre
                    tabIndex={0}
                    role="group"
                    aria-label="SQL query"
                    className="mt-2 overflow-x-auto rounded-xl bg-ink p-3 font-mono text-[12px] leading-relaxed text-paper"
                  >
                    {item.sql}
                  </pre>
                </details>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
