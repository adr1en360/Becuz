"use client";

import type { CSSProperties } from "react";
import { demo, demoDays } from "@/lib/demo-report";
import { formatPct, formatRange } from "@/lib/format";
import { useSeen } from "@/lib/use-seen";
import { Figure } from "./figure";

type Row = { label: string; value: number; from: number; to: number; kind: "total" | "drop" | "rise" };

// A bridge chart from the saved run: the usual profit, each supported cause taken off it in turn, the part no cause
// explains, then this period's profit. Every label and value is a field of the run; the bar positions are only
// geometry for drawing them.
const { headline, causes, convergence, frame } = demo;
const rows: Row[] = [{ label: "Usually", value: headline.baseline_ngn, from: 0, to: headline.baseline_ngn, kind: "total" }];
let level = headline.baseline_ngn;
for (const c of causes) {
  rows.push({ label: c.title, value: c.impact_ngn, from: level + c.impact_ngn, to: level, kind: "drop" });
  level += c.impact_ngn;
}
if (Math.abs(convergence.unexplained_ngn) >= 1) {
  const u = convergence.unexplained_ngn;
  rows.push({ label: "Not explained by a cause", value: u, from: Math.min(level, level + u), to: Math.max(level, level + u), kind: u < 0 ? "drop" : "rise" });
}
rows.push({ label: `These ${demoDays} days`, value: headline.current_ngn, from: 0, to: headline.current_ngn, kind: "total" });
const scale = Math.max(...rows.map((r) => r.to));

const barColour = { total: "bg-ink", drop: "bg-accent", rise: "bg-muted" };

export function HeroBridge() {
  const [ref, seen] = useSeen<HTMLDivElement>(0.2);
  return (
    <div ref={ref} data-seen={seen} className="rounded-[2rem] bg-paper p-6 text-ink sm:p-7">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-display text-xl font-bold [font-stretch:110%]">Where the profit went</p>
        <p className="font-mono text-xs text-muted">{formatRange(frame.period_start, frame.period_end)}</p>
      </div>
      <p className="mt-1 font-mono text-xs text-muted">Demo data from a synthetic shop</p>

      <ol className="mt-6 flex flex-col gap-4">
        {rows.map((row, i) => {
          const last = i === rows.length - 1;
          const style = {
            "--d": `${300 + i * 260}ms`,
            left: `${(row.from / scale) * 100}%`,
            width: `${Math.max(0.8, ((row.to - row.from) / scale) * 100)}%`,
          } as CSSProperties;
          return (
            <li key={row.label} className="bridge-row" style={{ "--d": `${200 + i * 260}ms` } as CSSProperties}>
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className={`min-w-0 truncate ${last || i === 0 ? "font-bold" : ""}`}>{row.label}</span>
                <span className={`num shrink-0 font-mono font-medium ${row.kind === "drop" ? "text-accent" : ""} ${last ? "text-base font-bold" : ""}`}>
                  {row.kind === "drop" ? "−" : row.kind === "rise" ? "+" : ""}
                  <Figure value={Math.abs(row.value)} kind="naira" />
                </span>
              </div>
              <div className="relative mt-1.5 h-3 rounded-full bg-ink/10">
                <span
                  className={`bridge-bar absolute inset-y-0 rounded-full ${barColour[row.kind]} ${row.kind === "drop" ? "origin-right" : "origin-left"} ${last ? "bg-accent" : ""}`}
                  style={style}
                />
              </div>
            </li>
          );
        })}
      </ol>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-2 border-t-2 border-dashed border-ink/20 pt-4 font-mono text-xs text-muted">
        <span>
          Down <span className="num font-semibold text-accent">{formatPct(headline.change_pct ?? 0)}</span>
        </span>
        <span>{formatPct(convergence.explained_pct)} of the change explained</span>
      </div>
    </div>
  );
}
