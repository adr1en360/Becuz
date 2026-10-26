"use client";

import { useState } from "react";
import { AltArrowDownIcon, ArrowRightIcon, DatabaseIcon } from "@solar-icons/react/outline";
import { SAMPLE_SCENARIOS } from "@/lib/api";

const EXAMPLE_CHIPS = [
  "Why is my profit down?",
  "How is my shop doing?",
  "Where did my money go?",
] as const;

const PERIODS = [
  { id: "2d", label: "2 days", enabled: false, tip: "Pending on server (requires flexible date window)" },
  { id: "1w", label: "1 week", enabled: true, tip: "7 days vs previous 4 weeks" },
  { id: "2w", label: "2 weeks", enabled: false, tip: "Pending on server" },
  { id: "custom", label: "Custom", enabled: false, tip: "Pending on server" },
] as const;

type Props = {
  running: boolean;
  showScenario: boolean;
  sampleMode?: boolean;
  note?: string;
  alert?: string | null;
  onSubmit: (question: string, scenario?: string) => void;
};

const field = "rounded-2xl border border-desk-line bg-desk-2 text-paper focus:border-flare transition-colors";

export function Composer({ running, showScenario, sampleMode = true, note, alert, onSubmit }: Props) {
  const [question, setQuestion] = useState("Why is my profit down?");
  const [scenario, setScenario] = useState<string>(SAMPLE_SCENARIOS[0]);
  const [period, setPeriod] = useState<string>("1w");
  const ready = question.trim().length > 0 && !running;

  return (
    <form
      className="flex flex-col gap-4"
      aria-describedby="composer-note"
      onSubmit={(event) => {
        event.preventDefault();
        if (ready) onSubmit(question.trim(), showScenario ? scenario : undefined);
      }}
    >
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2">
          <label htmlFor="question" className="text-sm font-semibold text-paper">
            Your question
          </label>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-desk-line px-2.5 py-0.5 text-xs text-desk-muted">
              <DatabaseIcon size={14} aria-hidden />
              Synthetic data
            </span>
            {sampleMode && (
              <span className="inline-flex items-center rounded-full border border-flare/50 bg-flare/10 px-2.5 py-0.5 text-xs font-medium text-flare">
                Sample mode
              </span>
            )}
          </div>
        </div>

        <textarea
          id="question"
          name="question"
          rows={2}
          maxLength={500}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask why your profit moved..."
          className={`${field} w-full resize-none px-4 py-3 text-base leading-snug`}
        />

        {/* 3 Example chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-desk-muted">Try:</span>
          {EXAMPLE_CHIPS.map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => setQuestion(chip)}
              className="rounded-full border border-desk-line bg-desk-2/60 px-3 py-1 text-xs text-desk-muted transition-colors hover:border-flare hover:text-paper active:scale-95"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Off-topic or 400 error banner */}
      {alert && (
        <div role="alert" className="rounded-2xl border border-flare bg-flare/10 px-4 py-3 text-sm text-paper">
          <p className="font-semibold text-flare">Unable to investigate:</p>
          <p className="mt-1">{alert}</p>
        </div>
      )}

      {/* Period picker & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-desk-line/50 pt-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-desk-muted">Period:</span>
            <div className="inline-flex rounded-full border border-desk-line bg-desk-2 p-0.5" role="radiogroup" aria-label="Investigation period">
              {PERIODS.map((p) => {
                const active = period === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    disabled={!p.enabled}
                    title={p.tip}
                    onClick={() => p.enabled && setPeriod(p.id)}
                    className={`rounded-full px-3 py-1 text-xs font-semibold transition-all ${
                      active
                        ? "bg-paper text-ink shadow-sm"
                        : p.enabled
                          ? "text-desk-muted hover:text-paper"
                          : "cursor-not-allowed text-desk-muted/40"
                    }`}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          {showScenario && (
            <div className="flex items-center gap-1.5">
              <label htmlFor="scenario" className="text-xs font-medium text-desk-muted">
                Scenario:
              </label>
              <div className="relative">
                <select
                  id="scenario"
                  value={scenario}
                  onChange={(event) => setScenario(event.target.value)}
                  className="h-8 appearance-none rounded-full border border-desk-line bg-desk-2 pl-3 pr-7 text-xs text-paper focus:border-flare"
                >
                  {SAMPLE_SCENARIOS.map((id) => (
                    <option key={id} value={id}>
                      {id}
                    </option>
                  ))}
                </select>
                <AltArrowDownIcon size={14} className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-desk-muted" aria-hidden />
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={!ready}
          className="inline-flex h-10 items-center gap-2 rounded-full bg-flare px-5 text-sm font-bold text-desk transition-colors hover:bg-paper active:scale-95 disabled:cursor-not-allowed disabled:bg-desk-2 disabled:text-desk-muted"
        >
          {running ? "Investigating..." : "Investigate"}
          <ArrowRightIcon size={16} aria-hidden />
        </button>
      </div>

      {note && (
        <p id="composer-note" role="status" className="text-xs text-desk-muted">
          {note}
        </p>
      )}
    </form>
  );
}
