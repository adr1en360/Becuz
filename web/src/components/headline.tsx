import type { Investigation } from "@/lib/investigation";
import { formatNaira, formatRange } from "@/lib/format";

const relation = { down: "below", up: "above", flat: "in line with" } as const;

export function Headline({ data }: { data: Investigation }) {
  const { headline, frame, summary } = data;
  const flat = headline.direction === "flat";
  return (
    <section aria-labelledby="headline">
      <h1 id="headline" className="text-balance text-3xl font-bold leading-[1.15] tracking-[-0.02em] sm:text-4xl">
        Profit this week was <span className="num">{formatNaira(headline.current_ngn)}</span>
        {flat ? ", " : ", "}
        {!flat && (
          <span className={headline.direction === "down" ? "text-accent" : undefined}>
            <span className="num">{formatNaira(headline.change_ngn)}</span>{" "}
          </span>
        )}
        {relation[headline.direction]} your <span className="whitespace-nowrap">4-week</span> average of <span className="num">{formatNaira(headline.baseline_ngn)}</span>.
      </h1>
      <p className="mt-3 text-sm text-muted">
        {formatRange(frame.period_start, frame.period_end)}, compared with {formatRange(frame.baseline_start, frame.baseline_end)}.
        You asked: &ldquo;{frame.question}&rdquo;
      </p>
      <p className="mt-6 max-w-prose text-lg leading-relaxed">{summary.what_happened}</p>
      <ul className="mt-4 max-w-prose list-disc space-y-1 pl-5 text-muted">
        {summary.why.map((reason) => <li key={reason}>{reason}</li>)}
      </ul>
    </section>
  );
}
