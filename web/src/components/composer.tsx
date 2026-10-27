"use client";

import { useRef, useState } from "react";
import { ArrowRightIcon } from "@solar-icons/react/outline";
import { SAMPLE_SCENARIOS } from "@/lib/api";

// Two why-questions start an investigation; the other two get a direct answer from the records.
const SUGGESTIONS = [
  "Why is my profit down?",
  "What sold the most?",
  "Is any money missing?",
  "What are my biggest expenses?",
] as const;

const PERIODS = [2, 7, 14, 28] as const;

export type Period = { days: number; period_start?: string };

type Props = {
  running: boolean;
  showScenario: boolean;
  sampleMode?: boolean;
  note?: string;
  alert?: string | null;
  onSubmit: (question: string, scenario: string | undefined, period: Period) => void;
};

const label = "text-xs font-semibold uppercase tracking-[0.14em] text-desk-muted lg:[@media(min-height:930px)]:text-[0.8rem]";
const segment = (on: boolean) =>
  `h-9 rounded-full text-sm font-semibold transition-colors lg:[@media(min-height:930px)]:h-10 lg:[@media(min-height:930px)]:text-[0.95rem] ${on ? "bg-paper text-ink" : "text-desk-muted hover:text-paper"}`;

export function Composer({ running, showScenario, sampleMode = true, note, alert, onSubmit }: Props) {
  const [question, setQuestion] = useState("Why is my profit down?");
  const [scenario, setScenario] = useState<string>(SAMPLE_SCENARIOS[0]);
  const [days, setDays] = useState(7);
  const [custom, setCustom] = useState(false);
  const [start, setStart] = useState("");
  const box = useRef<HTMLTextAreaElement>(null);
  const ready = question.trim().length > 0 && !running;

  function submit() {
    if (!ready) return;
    onSubmit(question.trim(), showScenario ? scenario : undefined, { days, period_start: custom && start ? start : undefined });
  }

  return (
    <form
      className="flex flex-col gap-5 lg:gap-[clamp(0.8rem,2vh,1.6rem)]"
      aria-describedby="composer-note"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <div className="rounded-3xl border-2 border-desk-line bg-desk-2 p-2 transition-colors focus-within:border-flare lg:[@media(min-height:930px)]:p-3">
        <label htmlFor="question" className="sr-only">
          Your question
        </label>
        <textarea
          ref={box}
          id="question"
          name="question"
          rows={2}
          maxLength={500}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
          placeholder="Ask about your shop's money..."
          className="block w-full resize-none bg-transparent px-3 pt-2 text-lg leading-snug text-paper placeholder:text-desk-muted focus:outline-none lg:[@media(min-height:930px)]:min-h-20 lg:[@media(min-height:930px)]:px-4 lg:[@media(min-height:930px)]:pt-3 lg:[@media(min-height:930px)]:text-xl"
        />
        <div className="flex items-center justify-between gap-2 pl-3">
          <span className="font-mono text-xs text-desk-muted">
            {custom && start ? `from ${start}, ` : ""}
            {days} days{showScenario ? `, shop ${scenario}` : ""}
          </span>
          <button
            type="submit"
            disabled={!ready}
            className="inline-flex h-11 items-center gap-2 rounded-full bg-flare px-5 font-bold lg:[@media(min-height:930px)]:h-12 lg:[@media(min-height:930px)]:px-6 lg:[@media(min-height:930px)]:text-lg text-desk transition-[background-color,transform] duration-150 hover:bg-paper active:scale-[0.97] disabled:cursor-not-allowed disabled:bg-desk disabled:text-desk-muted"
          >
            {running ? "Investigating..." : "Investigate"}
            <ArrowRightIcon size={18} aria-hidden />
          </button>
        </div>
      </div>

      {alert && (
        <div role="alert" className="rounded-2xl border border-flare bg-flare/10 px-4 py-3 text-sm text-paper">
          {alert}
        </div>
      )}

      <div>
        <p className={label}>Try asking</p>
        <div className="mt-2 grid grid-cols-2 gap-2 lg:[@media(min-height:930px)]:mt-3 lg:[@media(min-height:930px)]:gap-3">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={question === s}
              onClick={() => {
                setQuestion(s);
                box.current?.focus();
              }}
              className={`rounded-2xl border px-3 py-2 text-left text-sm leading-snug transition-colors lg:[@media(min-height:930px)]:px-4 lg:[@media(min-height:930px)]:py-2.5 lg:[@media(min-height:930px)]:text-[0.95rem] ${
                question === s ? "border-flare text-paper" : "border-desk-line text-desk-muted hover:border-paper/60 hover:text-paper"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className={label}>Period</p>
        <div className="mt-2 grid grid-cols-5 rounded-full border border-desk-line p-0.5 lg:[@media(min-height:930px)]:mt-3 lg:[@media(min-height:930px)]:p-1" role="group" aria-label="Investigation period">
          {PERIODS.map((n) => (
            <button
              key={n}
              type="button"
              aria-pressed={!custom && days === n}
              onClick={() => {
                setCustom(false);
                setDays(n);
              }}
              className={segment(!custom && days === n)}
            >
              {n}d
              <span className="sr-only"> days</span>
            </button>
          ))}
          <button type="button" aria-pressed={custom} onClick={() => setCustom(true)} className={segment(custom)}>
            Custom
          </button>
        </div>
        {custom && (
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-desk-muted">
            <label htmlFor="period-start">From</label>
            <input
              id="period-start"
              type="date"
              value={start}
              onChange={(event) => setStart(event.target.value)}
              className="h-9 rounded-full border border-desk-line bg-desk-2 px-3 text-sm text-paper [color-scheme:dark] focus:border-flare"
            />
            <label htmlFor="period-days">for</label>
            <input
              id="period-days"
              type="number"
              min={1}
              max={28}
              value={days}
              onChange={(event) => setDays(Math.min(28, Math.max(1, Number(event.target.value) || 1)))}
              className="h-9 w-16 rounded-full border border-desk-line bg-desk-2 px-3 text-sm text-paper focus:border-flare"
            />
            <span>days</span>
          </div>
        )}
      </div>

      {showScenario && (
        <div>
          <p className={label} id="scenario-label">
            Test shop
          </p>
          <div className="mt-2 grid grid-cols-5 rounded-full border border-desk-line p-0.5 lg:[@media(min-height:930px)]:mt-3 lg:[@media(min-height:930px)]:p-1" role="group" aria-labelledby="scenario-label">
            {SAMPLE_SCENARIOS.map((id) => (
              <button key={id} type="button" aria-pressed={scenario === id} onClick={() => setScenario(id)} className={segment(scenario === id)}>
                {id}
              </button>
            ))}
          </div>
        </div>
      )}

      {note && (
        <p id="composer-note" role="status" className="flex items-start gap-2 text-xs leading-relaxed text-desk-muted lg:[@media(min-height:930px)]:text-sm">
          <span aria-hidden className={`mt-1 size-2 shrink-0 rounded-full ${sampleMode ? "bg-flare" : "bg-paper"}`} />
          {note}
        </p>
      )}
    </form>
  );
}
