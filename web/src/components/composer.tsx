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

const field = "rounded-2xl border border-desk-line bg-desk-2 text-paper";

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
        className={`${field} w-full resize-none px-4 py-3.5 text-lg leading-snug`}
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
              className="h-11 appearance-none rounded-full border border-desk-line bg-desk-2 pl-4 pr-10 text-base text-paper"
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
          className="inline-flex h-12 items-center gap-2 rounded-full bg-flare px-6 text-base font-bold text-desk transition-colors hover:bg-paper disabled:cursor-not-allowed disabled:bg-desk-2 disabled:text-desk-muted"
        >
          {running ? "Investigating" : "Investigate"}
          <ArrowRightIcon size={18} aria-hidden />
        </button>
        <p id="composer-note" role="status" className="max-w-sm text-sm text-desk-muted">
          {note}
        </p>
      </div>
    </form>
  );
}
