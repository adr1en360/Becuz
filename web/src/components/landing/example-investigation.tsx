import { Stamp } from "@/components/stamp";
import { demo } from "@/lib/demo-report";
import { Figure } from "./figure";
import { Reveal } from "./reveal";

const cause = demo.causes[0];
const cash = demo.cash_gaps?.[0];

export function ExampleInvestigation() {
  return (
    <section aria-labelledby="example" className="mx-auto w-full max-w-5xl px-4 sm:px-8">
      <Reveal className="flex flex-wrap items-end justify-between gap-4">
        <h2 id="example" className="max-w-xl text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-6xl">
          What an investigation looks like
        </h2>
        <div className="flex items-center gap-3">
          <Stamp label="Demo data" rotate={-3} />
          <p className="font-mono text-xs text-muted">From a synthetic shop</p>
        </div>
      </Reveal>

      <ul className="mt-12 flex flex-col">
        <Reveal as="li" delay={0} className="cut-line py-8 first:border-0">
          <h3 className="max-w-2xl text-balance font-display text-2xl font-bold leading-tight [font-stretch:110%] sm:text-3xl">
            {cause.title}.
          </h3>
          <p className="num mt-4 font-mono text-2xl font-medium text-accent sm:text-3xl">Cost: <Figure value={Math.abs(cause.impact_ngn)} kind="naira" />.</p>
        </Reveal>
        {cash && (
          <Reveal as="li" delay={70} className="cut-line py-8">
            <h3 className="max-w-3xl text-balance font-display text-2xl font-bold leading-tight [font-stretch:110%] sm:text-3xl">
              <Figure value={Math.abs(cash.impact_ngn)} kind="naira" /> from {cash.evidence[0].row_ids.length} transfer sales was recorded at the till but never reached the bank.
            </h3>
            <p className="mt-4 max-w-xl text-lg leading-snug text-muted">
              The sales still count toward profit, but this money is missing from your account.
            </p>
          </Reveal>
        )}
        <Reveal as="li" delay={140} className="cut-line flex flex-wrap items-center justify-between gap-4 py-8">
          <h3 className="max-w-2xl text-balance font-display text-2xl font-bold leading-tight [font-stretch:110%] sm:text-3xl">
            Some causes were tested and ruled out, so you do not chase the wrong fix.
          </h3>
          <Stamp label="Ruled out" tone="accent" rotate={4} />
        </Reveal>
      </ul>
    </section>
  );
}
