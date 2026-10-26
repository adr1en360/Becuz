"use client";

import { useSeen } from "@/lib/use-seen";

// A picture of the two weeks, drawn from the same two figures as the sentence above it. No new numbers.
const usual = 379412;
const thisWeek = 241717;
const share = (thisWeek / usual) * 100;

export function HeroBars() {
  const [ref, seen] = useSeen<HTMLDivElement>();
  return (
    <div ref={ref} aria-hidden className="mt-6 flex flex-col gap-3 font-mono text-xs text-muted">
      <div>
        <p>A usual week</p>
        <div className="mt-1.5 h-3.5 rounded-full bg-ink/15">
          <div data-seen={seen} style={{ transitionDelay: "450ms" }} className="draw h-full w-full rounded-full bg-ink" />
        </div>
      </div>
      <div>
        <p>This week</p>
        <div className="mt-1.5 flex h-3.5 gap-1">
          <div
            data-seen={seen}
            style={{ width: `${share}%`, transitionDelay: "600ms" }}
            className="draw h-full rounded-full bg-accent"
          />
          <div
            data-seen={seen}
            className="h-full flex-1 rounded-full border-2 border-dashed border-accent opacity-0 transition-opacity delay-[1300ms] duration-500 data-[seen=true]:opacity-100 motion-reduce:opacity-100 motion-reduce:transition-none"
          />
        </div>
      </div>
    </div>
  );
}
