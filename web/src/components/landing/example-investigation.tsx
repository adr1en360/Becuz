import Link from "next/link";
import { ArrowRightIcon } from "@solar-icons/react/outline";
import { Stamp } from "@/components/stamp";
import { Figure } from "./figure";
import { Reveal } from "./reveal";

export function ExampleInvestigation() {
  return (
    <section id="example" aria-labelledby="example" className="mx-auto w-full max-w-5xl px-4 sm:px-8">
      <Reveal className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="font-mono text-xs uppercase tracking-widest text-muted">Receipt view</span>
          <h2 id="example" className="mt-1 max-w-xl text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-6xl text-ink">
            What an investigation looks like
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <Stamp label="Demo data" rotate={-3} />
          <p className="font-mono text-xs text-muted">From a synthetic shop</p>
        </div>
      </Reveal>

      <ul className="mt-12 flex flex-col">
        <Reveal as="li" delay={0} className="cut-line py-8 first:border-0">
          <h3 className="max-w-2xl text-balance font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%] sm:text-3xl">
            A supplier raised the unit cost of a product.
          </h3>
          <p className="num mt-4 font-mono text-2xl font-medium text-accent sm:text-3xl">
            Cost: <Figure value={46992} kind="naira" />.
          </p>
        </Reveal>
        <Reveal as="li" delay={70} className="cut-line py-8">
          <h3 className="max-w-3xl text-balance font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%] sm:text-3xl">
            <Figure value={28360} kind="naira" /> from 6 transfer sales was recorded at the till but never reached the bank.
          </h3>
          <p className="mt-4 max-w-xl text-lg leading-snug text-muted">
            The sales still count toward profit, but this money is missing from your account.
          </p>
        </Reveal>
        <Reveal as="li" delay={140} className="cut-line flex flex-wrap items-center justify-between gap-4 py-8">
          <h3 className="max-w-2xl text-balance font-display text-2xl font-bold leading-tight text-ink [font-stretch:110%] sm:text-3xl">
            Some causes were tested and ruled out, so you do not chase the wrong fix.
          </h3>
          <Stamp label="Ruled out" tone="accent" rotate={4} />
        </Reveal>
      </ul>

      <Reveal delay={200} className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t-2 border-dashed border-ink/40 pt-6">
        <p className="text-sm font-mono text-muted">
          Every number is traced to a query, a record, and an independent Checker rating.
        </p>
        <Link
          href="/investigate"
          className="inline-flex h-11 items-center gap-2 rounded-full bg-ink px-6 text-sm font-bold text-paper transition-colors hover:bg-accent active:scale-95"
        >
          Explore this investigation
          <ArrowRightIcon size={16} aria-hidden />
        </Link>
      </Reveal>
    </section>
  );
}
