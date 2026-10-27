"use client";

import { useState, type CSSProperties } from "react";
import { CheckCircleIcon } from "@solar-icons/react/bold";
import { PrinterMinimalisticIcon } from "@solar-icons/react/outline";
import { Barcode } from "@/components/barcode";
import { demo } from "@/lib/demo-report";
import { formatNaira, formatRange } from "@/lib/format";
import { Figure } from "./figure";
import { HeroBars } from "./hero-bars";
import { Tilt } from "./tilt";

const at = (ms: number) => ({ "--d": `${ms}ms` }) as CSSProperties;
const { headline, frame, causes, ruled_out, run_id } = demo;
const cash = demo.cash_gaps ?? [];
// Rows print one after another, 110 ms apart: causes, then missing cash, then ruled out, then the footer.
const row = (n: number) => 1010 + n * 110;

// The saved s01 run, printed line by line and then re-checked: the scan line sweeps the receipt and each supported
// cause gets its tick, the way the Checker re-runs every query before a cause is shown. Plays once; "Print again"
// replays it. Every figure comes from the saved run.
export function HeroReceipt() {
  const [copy, setCopy] = useState(0);
  const checked = 2300;

  return (
    <div className="flex flex-col items-center gap-3 lg:items-end">
      <Tilt className="relative w-full">
        <div aria-hidden className="relative z-10 h-4 rounded-full border border-desk-line bg-desk-2" />
        <div key={copy} className="receipt slot paper print-slow relative -mt-2 px-6 pb-6 pt-6 sm:px-7">
          <div className="row-in flex flex-wrap items-center justify-between gap-2" style={at(250)}>
            <span className="stamp text-ink" data-seen="true" style={{ "--r": "-2deg", animationDelay: "300ms" } as CSSProperties}>
              Demo data
            </span>
            <p className="font-mono text-xs text-muted">
              Synthetic shop, {formatRange(frame.period_start, frame.period_end)}
            </p>
          </div>

          <p className="row-in mt-4 font-mono text-xs uppercase tracking-[0.16em] text-muted" style={at(420)}>
            Profit, these {frame.days ?? 7} days
          </p>
          <p className="row-in mt-1 font-display text-4xl font-extrabold tracking-tight [font-stretch:110%] xl:text-[2.6rem]" style={at(480)}>
            <Figure value={headline.current_ngn} kind="naira" />
          </p>
          <p className="row-in mt-1 text-sm text-muted" style={at(560)}>
            Usually <Figure value={headline.baseline_ngn} kind="naira" />
          </p>
          <p className="row-in cut-line mt-3 pt-3 text-lg font-bold text-accent" style={at(640)}>
            {headline.direction === "up" ? "Up" : "Down"} <Figure value={Math.abs(headline.change_ngn)} kind="naira" />
            {headline.change_pct !== null && (
              <>
                {" · "}
                <Figure value={Math.abs(headline.change_pct)} kind="percent" />%
              </>
            )}
          </p>

          <div className="row-in lg:[@media(max-height:780px)]:hidden" style={at(720)}>
            <HeroBars />
          </div>

          <div className="relative mt-4 border-t-2 border-dashed border-ink/30 pt-3 font-mono text-xs leading-snug">
            <p className="row-in text-xs uppercase tracking-[0.16em] text-muted" style={at(820)}>
              Why
            </p>
            <ul className="mt-2 flex flex-col gap-1.5">
              {causes.map((c, i) => (
                <li key={c.cause_id} className="row-in flex items-baseline gap-2" style={at(row(i))}>
                  <CheckCircleIcon size={14} className="tick shrink-0 self-center text-ink" style={at(checked + i * 140)} aria-hidden />
                  <span className="min-w-0">{c.title}</span>
                  <span className="leader" aria-hidden />
                  <span className="num shrink-0 font-medium text-accent">−{formatNaira(c.impact_ngn)}</span>
                </li>
              ))}
              {cash.map((g, i) => (
                <li key={g.cause_id} className="row-in flex items-baseline gap-2" style={at(row(causes.length + i))}>
                  <CheckCircleIcon size={14} className="tick shrink-0 self-center text-ink" style={at(checked + causes.length * 140)} aria-hidden />
                  <span className="min-w-0">Missing from the bank</span>
                  <span className="leader" aria-hidden />
                  <span className="num shrink-0 font-medium">{formatNaira(g.impact_ngn)}</span>
                </li>
              ))}
              {ruled_out.map((r, i) => (
                <li key={r.cause_id} className="row-in flex items-baseline gap-2 text-muted" style={at(row(causes.length + cash.length + i))}>
                  <span className="size-3.5 shrink-0" aria-hidden />
                  <span className="min-w-0">
                    <span className="strike" style={at(checked + 500 + i * 140)}>
                      {r.hypothesis}
                    </span>
                  </span>
                  <span className="leader" aria-hidden />
                  <span className="shrink-0">ruled out</span>
                </li>
              ))}
            </ul>
            <span aria-hidden className="scan" style={at(1500)} />
          </div>

          <div className="row-in mt-4 flex items-end justify-between gap-4" style={at(row(causes.length + cash.length + ruled_out.length))}>
            <div className="text-ink [&_svg]:h-7 [&_svg]:w-auto">
              <Barcode seed={run_id} />
            </div>
            <span className="stamp text-accent" data-seen="true" style={{ "--r": "-6deg", animationDelay: `${checked + 900}ms` } as CSSProperties}>
              Checked twice
            </span>
          </div>
        </div>
      </Tilt>
      <button
        type="button"
        onClick={() => setCopy((n) => n + 1)}
        className="inline-flex h-9 items-center gap-2 rounded-full border border-desk-line px-4 text-sm lg:[@media(max-height:780px)]:hidden font-semibold text-desk-muted transition-[color,border-color,transform] duration-150 hover:border-paper hover:text-paper active:scale-[0.97]"
      >
        <PrinterMinimalisticIcon size={16} aria-hidden />
        Print it again
      </button>
    </div>
  );
}
