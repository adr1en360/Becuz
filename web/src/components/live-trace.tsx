"use client";

import { useEffect, useRef, useState } from "react";
import type { TraceEvent } from "@/lib/api";
import { AltArrowDownIcon, CheckCircleIcon, ClockCircleIcon } from "@solar-icons/react/outline";
import { causeName, describeAction, engineName, secondsSince } from "@/lib/trace";
import { Receipt, SectionTitle } from "./receipt";

export function LiveTrace({ events, busy = true }: { events: TraceEvent[]; busy?: boolean }) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showTechnical, setShowTechnical] = useState(false);

  // Auto-scroll to newest step
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [events.length]);

  // Only events that have `plain` (or retry notices) are shown by default
  const displayEvents = events.filter((e) => Boolean(e.plain) || e.retry_count > 0);

  return (
    <Receipt>
      <div className="flex items-center justify-between gap-4">
        <SectionTitle id="live-heading">Investigation in progress</SectionTitle>
        <button
          type="button"
          onClick={() => setShowTechnical((prev) => !prev)}
          className="inline-flex items-center gap-1.5 rounded-full border border-ink/30 px-3 py-1 font-mono text-xs text-muted hover:border-ink hover:text-ink active:scale-95"
        >
          {showTechnical ? "Hide technical details" : "Show technical details"}
          <AltArrowDownIcon
            size={14}
            className={`transition-transform duration-200 ${showTechnical ? "rotate-180" : ""}`}
            aria-hidden
          />
        </button>
      </div>

      <div className="mt-6" role="log" aria-live="polite" aria-labelledby="live-heading">
        {displayEvents.length === 0 ? (
          <div className="flex items-center gap-3 py-4 text-sm text-muted">
            <span className="inline-block size-2 animate-ping rounded-full bg-accent" aria-hidden />
            <span>Starting investigation. Querying your records through Zetaris...</span>
          </div>
        ) : (
          <ol className="flex flex-col gap-5">
            {displayEvents.map((e, i) => {
              const isRetry = e.retry_count > 0 && e.status !== "success";
              const plainText = isRetry
                ? "The data source was busy, so Becuz is trying again."
                : e.plain ?? e.output_summary;

              const engine = engineName(e);
              const cause = causeName(e);
              const isLatest = i === displayEvents.length - 1 && busy;

              return (
                <li key={`${e.timestamp}-${i}`} className="flex gap-3 text-sm">
                  <div className="mt-0.5 shrink-0">
                    {isLatest ? (
                      <span className="flex size-5 items-center justify-center rounded-full bg-accent/20">
                        <span className="size-2 rounded-full bg-accent animate-pulse" />
                      </span>
                    ) : (
                      <CheckCircleIcon size={20} className="text-ink" aria-hidden />
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-ink leading-snug">{plainText}</p>

                    {showTechnical && (
                      <div className="mt-2 rounded-xl bg-paper-2 p-2.5 font-mono text-xs text-muted">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold text-ink">
                            {e.agent_name} · {describeAction(e).toLowerCase()}
                          </span>
                          {cause && <span className="text-accent">{cause}</span>}
                          <span className="text-[11px] text-muted">+{secondsSince(events[0], e)}s</span>
                        </div>
                        <p className="mt-1 font-sans text-xs">{e.output_summary}</p>
                        <ul className="mt-1.5 flex flex-wrap gap-1.5 text-[11px]">
                          {engine && <li className="rounded bg-paper px-1.5 py-0.5 border border-ink/20">{engine}</li>}
                          {e.model && <li className="rounded bg-paper px-1.5 py-0.5 border border-ink/20">{e.model}</li>}
                          {e.via && <li className="rounded bg-paper px-1.5 py-0.5 border border-ink/20">via {e.via}</li>}
                        </ul>
                      </div>
                    )}
                  </div>
                </li>
              );
            })}

            {busy && (
              <li className="flex items-center gap-3 pt-2 text-sm text-muted">
                <span className="size-2 rounded-full bg-accent animate-ping" aria-hidden />
                <span>Checking records for the next cause...</span>
              </li>
            )}
          </ol>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mt-8 flex items-center justify-between border-t border-rule pt-4 text-xs font-mono text-muted">
        <span className="flex items-center gap-1.5">
          <ClockCircleIcon size={14} aria-hidden />
          Live trace stream
        </span>
        <span className="uppercase tracking-[0.16em]">Printing receipt</span>
      </div>
    </Receipt>
  );
}
