"use client";

import { demo, demoDays } from "@/lib/demo-report";
import { useSeen } from "@/lib/use-seen";

// A picture of the two periods, drawn from the same two figures as the sentence above it. No new numbers.
const share = Math.min(100, (demo.headline.current_ngn / demo.headline.baseline_ngn) * 100);

export function HeroBars() {
  const [ref, seen] = useSeen<HTMLDivElement>();
  return (
    <div ref={ref} aria-hidden className="mt-4 grid grid-cols-[5.5rem_minmax(0,1fr)] items-center gap-x-3 gap-y-2 font-mono text-xs text-muted">
      <p>Usual</p>
      <div className="h-2.5 rounded-full bg-ink/15">
        <div data-seen={seen} style={{ transitionDelay: "450ms" }} className="draw h-full w-full rounded-full bg-ink" />
      </div>
      <p>These {demoDays} days</p>
      <div className="flex h-2.5 gap-1">
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
  );
}
