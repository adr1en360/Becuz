"use client";

import { useState } from "react";
import { AltArrowDownIcon, ArrowRightIcon } from "@solar-icons/react/outline";
import { SAMPLE_SCENARIOS } from "@/lib/api";

type Props = {
  running: boolean;
  showScenario: boolean;
  note: string;
  onSubmit: (question: string, scenario?: string) => void;
};

export function Composer({ running, showScenario, note, onSubmit }: Props) {
  const [question, setQuestion] = useState("Why is my profit down this week?");
  const [scenario, setScenario] = useState<string>(SAMPLE_SCENARIOS[0]);
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
      <label htmlFor="question" className="text-sm font-semibold">
        Your question
      </label>
      <textarea
        id="question"
        name="question"
        rows={3}
        maxLength={500}
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        className="w-full resize-none rounded-2xl border border-rule-strong bg-field px-4 py-3.5 text-lg leading-snug text-ink"
      />
      {showScenario && (
        <div className="flex flex-col gap-2">
          <label htmlFor="scenario" className="text-sm font-semibold">
            Test week
          </label>
          <div className="relative w-fit">
            <select
              id="scenario"
              value={scenario}
              onChange={(event) => setScenario(event.target.value)}
              className="h-11 appearance-none rounded-full border border-rule-strong bg-field pl-4 pr-10 text-base"
            >
              {SAMPLE_SCENARIOS.map((id) => (
                <option key={id} value={id}>
                  Scenario {id}
                </option>
              ))}
            </select>
            <AltArrowDownIcon size={16} className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2" aria-hidden />
          </div>
        </div>
      )}
      <div className="flex flex-col items-start gap-3">
        <button
          type="submit"
          disabled={!ready}
          className="inline-flex h-12 items-center gap-2 rounded-full bg-ink px-6 text-base font-semibold text-paper transition-colors hover:bg-[#1d2f55] disabled:cursor-not-allowed disabled:bg-disabled disabled:text-disabled-text"
        >
          {running ? "Investigating" : "Investigate"}
          <ArrowRightIcon size={18} aria-hidden />
        </button>
        <p id="composer-note" role="status" className="max-w-sm text-sm text-muted">
          {note}
        </p>
      </div>
    </form>
  );
}
