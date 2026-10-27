import { demo } from "@/lib/demo-report";
import { Figure } from "./figure";
import { recordCount } from "./records-ticker";
import { Reveal } from "./reveal";
import { SplitHeading } from "./split-heading";

const tested = demo.causes.length + (demo.cash_gaps?.length ?? 0) + demo.ruled_out.length;
const stats = [
  { value: demo.stats.zetaris_queries, label: "queries run on the shop's records" },
  { value: tested, label: "possible causes tested" },
  { value: demo.ruled_out.length, label: "ruled out, so you skip the wrong fix" },
  { value: recordCount, label: "records cited as proof" },
];

// Counters from the example run. Each one is a count from the saved report, not a claim about other shops.
export function Numbers() {
  return (
    <section aria-labelledby="numbers" className="mx-auto w-full max-w-6xl px-4 py-24 sm:px-8 lg:py-32">
      <SplitHeading id="numbers" className="max-w-3xl text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-6xl">
        One question. Every number checked.
      </SplitHeading>
      <Reveal delay={120}>
        <p className="mt-5 max-w-xl text-lg leading-relaxed text-desk-muted">
          What it took to answer &ldquo;{demo.frame.question}&rdquo; for one synthetic shop, from the saved run.
        </p>
      </Reveal>
      <dl className="mt-14 grid grid-cols-2 gap-x-6 gap-y-12 lg:grid-cols-4">
        {stats.map((s, i) => (
          <Reveal key={s.label} delay={i * 110}>
            <span aria-hidden className="mb-5 block h-1 w-10 rounded-full bg-flare" />
            <dt className="sr-only">{s.label}</dt>
            <dd>
              <span className="block font-display text-6xl font-extrabold leading-none tracking-tight [font-stretch:120%] sm:text-7xl">
                <Figure value={s.value} kind="count" />
              </span>
              <span className="mt-3 block max-w-[12rem] text-desk-muted">{s.label}</span>
            </dd>
          </Reveal>
        ))}
      </dl>
    </section>
  );
}
