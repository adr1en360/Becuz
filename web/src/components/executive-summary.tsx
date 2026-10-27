"use client";

import { useState } from "react";
import type { Investigation } from "@/lib/investigation";
import { formatPct, formatSigned } from "@/lib/format";
import { natureLabel, originLabel } from "@/lib/labels";
import {
  AltArrowDownIcon,
  CheckSquareIcon,
  ClockCircleIcon,
  DatabaseIcon,
  PrinterIcon,
} from "@solar-icons/react/outline";
import { Barcode } from "./barcode";
import { ConfirmButton } from "./confirm-button";
import { Leader, SectionTitle } from "./receipt";

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

export function ExecutiveSummary({ data }: { data: Investigation }) {
  const { summary, stats, run_id, causes } = data;
  const [checkedActions, setCheckedActions] = useState<Record<number, boolean>>({});

  const toggleAction = (idx: number) => {
    setCheckedActions((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const models = Object.entries(stats.models);
  // A step can point at a cash gap as well as a profit cause, so look in both for its title.
  const titles = new Map([...causes, ...(data.cash_gaps ?? [])].map((c) => [c.cause_id, c.title]));

  return (
    <section aria-labelledby="exec-summary" className="flex flex-col gap-8">
      <SectionTitle id="exec-summary">Executive summary</SectionTitle>

      {/* 1. What happened */}
      <div className="flex flex-col gap-2">
        <h3 className="font-mono text-xs uppercase tracking-[0.16em] text-muted">What happened</h3>
        <p className="text-xl font-bold leading-snug text-ink sm:text-2xl">
          {summary.what_happened}
        </p>
      </div>

      {/* 2. Why: one card per cause */}
      {causes.length > 0 && (
        <div className="flex flex-col gap-3">
          <h3 className="font-mono text-xs uppercase tracking-[0.16em] text-muted">Why</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {causes.map((cause) => {
              const statusText = natureLabel[cause.nature];
              return (
                <div
                  key={cause.cause_id}
                  className="flex flex-col justify-between gap-3 rounded-2xl border border-rule bg-paper p-4"
                >
                  <div>
                    <div className="flex items-baseline justify-between gap-2">
                      <h4 className="font-display font-bold text-ink">{cause.title}</h4>
                      <span className="num font-mono font-bold text-accent">
                        {formatSigned(cause.impact_ngn)}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-muted">
                      {formatPct(cause.share_of_change_pct)} of change · {originLabel[cause.origin]}
                    </p>
                    <div className="mt-2 flex items-center gap-1.5">
                      <span className="rounded-full bg-paper-2 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-ink">
                        {statusText}
                      </span>
                    </div>
                  </div>
                  <div className="pt-2">
                    <ConfirmButton runId={run_id} causeId={cause.cause_id} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 3. What to do */}
      {summary.what_to_do.length > 0 && (
        <div className="flex flex-col gap-3">
          <h3 className="font-mono text-xs uppercase tracking-[0.16em] text-muted">What to do</h3>
          <ul className="flex flex-col gap-2.5">
            {summary.what_to_do.map((item, idx) => {
              const isChecked = !!checkedActions[idx];
              return (
                <li key={item.action}>
                  <label
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3.5 transition-colors ${
                      isChecked ? "border-rule bg-paper-2/60 text-muted" : "border-rule bg-paper text-ink hover:border-ink/40"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleAction(idx)}
                      className="mt-0.5 size-4 shrink-0 rounded accent-accent"
                    />
                    <span className="flex-1 text-sm leading-relaxed">
                      <span className={`font-medium ${isChecked ? "line-through" : ""}`}>{item.action}</span>
                      <span className="mt-1 block text-xs text-muted">Because: {titles.get(item.cause_id) ?? item.cause_id}</span>
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* 4. If you act on this (Expected outcome) */}
      {summary.outcome && (
        <div className="rounded-2xl border-2 border-accent/30 bg-accent/5 p-5 text-ink">
          <p className="font-mono text-xs font-bold uppercase tracking-[0.18em] text-accent">
            If you act on this
          </p>
          <p className="mt-2 text-base font-semibold leading-relaxed">
            {summary.outcome}
          </p>
        </div>
      )}

      {/* 5. Export PDF Button */}
      <div className="flex items-center justify-between border-t border-rule pt-6 print:hidden">
        <button
          type="button"
          onClick={() => window.print()}
          className="inline-flex h-11 items-center gap-2 rounded-full border-2 border-ink bg-paper px-6 text-sm font-bold text-ink transition-colors hover:bg-ink hover:text-paper active:scale-95"
        >
          <PrinterIcon size={18} aria-hidden />
          Export PDF / Print receipt
        </button>
      </div>

      {data.limitations.length > 0 && (
        <div className="rounded-2xl border-2 border-dashed border-ink/30 p-4">
          <p className="font-mono text-xs font-bold uppercase tracking-[0.16em] text-muted">Keep in mind</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink">
            {data.limitations.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 6. Run facts footer */}
      <div className="rounded-2xl border border-rule bg-paper-2/50 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-muted">
          <div className="flex flex-wrap items-center gap-4 sm:gap-6">
            <span className="flex items-center gap-1.5 text-ink font-semibold">
              <ClockCircleIcon size={16} aria-hidden />
              {formatDuration(stats.duration_s)}
            </span>
            <span className="flex items-center gap-1.5">
              <DatabaseIcon size={16} aria-hidden />
              {stats.zetaris_queries} Zetaris queries
            </span>
            <span className="flex items-center gap-1.5">
              <CheckSquareIcon size={16} aria-hidden />
              {stats.model_calls} model checks
            </span>
          </div>

          <details className="group">
            <summary className="inline-flex cursor-pointer items-center gap-1 font-sans text-xs font-semibold text-ink underline hover:text-accent">
              How this was run
              <AltArrowDownIcon
                size={12}
                className="transition-transform duration-200 group-open:rotate-180"
                aria-hidden
              />
            </summary>
            <div className="mt-3 flex flex-col gap-2 rounded-xl bg-paper p-3 text-xs font-mono text-muted">
              <Leader label="Mode" value={data.mode} />
              <Leader
                label="Data"
                value={`${data.synthetic ? "Synthetic" : "Real"}${
                  data.scenario ? `, ${data.scenario}` : ""
                }`}
              />
              <Leader
                label="Models"
                value={
                  models.length
                    ? models.map(([m, n]) => `${m} (${n})`).join(", ")
                    : "none used"
                }
              />
              <Leader label="Retries" value={stats.retries} />

              <div className="mt-2 flex flex-col items-center gap-1 pt-2">
                <Barcode seed={run_id} />
                <span className="text-[10px] tracking-widest">{run_id}</span>
              </div>
            </div>
          </details>
        </div>
      </div>
    </section>
  );
}
