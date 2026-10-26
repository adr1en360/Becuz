import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatRange } from "@/lib/format";
import { CountUp } from "./count-up";
import { Leader } from "./receipt";

const display = "font-display text-balance text-[2.25rem] font-extrabold leading-[0.95] tracking-[-0.02em] [font-stretch:125%] sm:text-6xl";

export function Headline({ data }: { data: Investigation }) {
  const { headline, frame, summary } = data;
  const amount = <CountUp value={Math.abs(headline.change_ngn)} format={formatNaira} />;
  return (
    <section aria-labelledby="headline">
      <h1 id="headline" tabIndex={-1} className={`${display} outline-none`}>
        {headline.direction === "flat" ? (
          "Profit held steady against your usual week."
        ) : (
          <>
            Profit {headline.direction === "down" ? "fell" : "rose"}{" "}
            <span className={`whitespace-nowrap ${headline.direction === "down" ? "text-accent" : ""}`}>{amount}</span>{" "}
            {headline.direction === "down" ? "below" : "above"} your usual week.
          </>
        )}
      </h1>

      <div className="mt-8 flex flex-col gap-2 text-lg">
        <Leader label="This week" value={formatNaira(headline.current_ngn)} />
        <Leader label="Your 4-week average" value={formatNaira(headline.baseline_ngn)} />
      </div>

      <ul className="mt-6 list-disc space-y-1.5 pl-5 text-lg marker:text-accent">
        {summary.why.map((reason) => <li key={reason}>{reason}</li>)}
      </ul>

      <p className="mt-6 text-sm text-muted">
        Compared with {formatRange(frame.baseline_start, frame.baseline_end)}. You asked: &ldquo;{frame.question}&rdquo;
      </p>
    </section>
  );
}
