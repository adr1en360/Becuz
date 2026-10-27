import Link from "next/link";
import { ArrowRightIcon, ScissorsIcon } from "@solar-icons/react/outline";
import { Barcode } from "@/components/barcode";
import { Stamp } from "@/components/stamp";
import { demo } from "@/lib/demo-report";
import { formatNaira } from "@/lib/format";
import { Reveal } from "./reveal";
import { SplitHeading } from "./split-heading";

const top = demo.causes[0];
const cash = demo.cash_gaps?.[0];
const heading = "text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-5xl";

function Row({ label, value, note, delay = 0, valueClass = "" }: { label: string; value: string; note?: string; delay?: number; valueClass?: string }) {
  return (
    <Reveal as="li" delay={delay}>
      <div className="flex items-baseline gap-2">
        <span className="font-semibold">{label}</span>
        <span className="leader" aria-hidden />
        <span className={`num shrink-0 font-mono text-sm font-medium uppercase ${valueClass}`}>{value}</span>
      </div>
      {note && <p className="mt-1.5 max-w-prose text-sm leading-relaxed text-muted">{note}</p>}
    </Reveal>
  );
}

const STEPS = [
  {
    title: "You ask",
    by: "Scout Intent",
    body: `You ask about your shop's money, for any 1 to 28 days. Becuz scopes the question, limits which records it may read, and compares the period with ${demo.frame.baseline ?? "the periods before"}.`,
  },
  {
    title: "It reads your records",
    by: "Zetaris",
    body: "Till sales, bank statement, supplier invoices and the expense book are queried where they live. Becuz can read them, never change them.",
  },
  {
    title: "It checks twice",
    by: "Nightshift + Nemotron",
    body: "A second agent re-runs every query. A claim whose numbers do not match is sent back or ruled out, and NVIDIA Nemotron rates how strong the evidence is.",
  },
  {
    title: "You get the receipt",
    by: "H-MEM",
    body: "Each cause comes with its naira effect and the records behind it, plus what was ruled out and one action per cause. Causes you confirm are checked first next time.",
  },
];

// Everything below the hero is one till receipt: line items, a printer log, a tear-off example and a footer.
export function LongReceipt() {
  return (
    <div className="px-3 sm:px-6">
      <article className="receipt paper mx-auto w-full max-w-[46rem] px-6 pb-14 pt-14 sm:px-12">
        <Reveal className="flex flex-col items-center gap-2 text-center">
          <span className="font-display text-4xl font-extrabold tracking-tight [font-stretch:125%]">
            Becuz<span className="text-accent">.</span>
          </span>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">Why your profit moved</p>
        </Reveal>

        <hr className="cut-line my-10 border-0" />

        <section aria-labelledby="rely">
          <SplitHeading id="rely" className={heading}>
            What you can rely on
          </SplitHeading>
          <ul className="mt-8 flex flex-col gap-6">
            <Row label="Every naira figure" value="from SQL" note="Computed from your records, not guessed by the model." />
            <Row label="Every cause" value="checked twice" delay={80} note="A second check re-runs the evidence before a cause is shown." />
            <Row label="Causes you confirm" value="checked first" delay={160} note="Becuz remembers them and tests them first next time." />
          </ul>
        </section>

        <hr className="cut-line my-12 border-0" />

        <section id="how-it-works" aria-labelledby="how-heading">
          <SplitHeading id="how-heading" className={heading}>
            How it works
          </SplitHeading>
          <ol className="relative mt-10 flex flex-col gap-10">
            <span aria-hidden className="absolute bottom-2 left-[1.05rem] top-2 w-0.5 rounded-full bg-ink/15">
              <span className="rail-fill block h-full w-full origin-top rounded-full bg-accent" />
            </span>
            {STEPS.map((step, i) => (
              <Reveal as="li" key={step.title} delay={i * 80} className="relative flex gap-5">
                <span className="num relative z-10 flex size-9 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-sm font-medium text-paper">
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2">
                    <h3 className="font-display text-2xl font-bold leading-tight [font-stretch:110%]">{step.title}</h3>
                    <span className="leader hidden sm:block" aria-hidden />
                    <span className="hidden shrink-0 font-mono text-xs uppercase tracking-wider text-accent sm:block">{step.by}</span>
                  </div>
                  <p className="mt-2 leading-relaxed text-muted">{step.body}</p>
                  <p className="mt-2 font-mono text-xs uppercase tracking-wider text-accent sm:hidden">{step.by}</p>
                </div>
              </Reveal>
            ))}
          </ol>
        </section>

        <div className="my-14 flex items-center gap-3 text-muted" aria-hidden>
          <ScissorsIcon size={20} />
          <span className="cut-line flex-1" />
          <span className="font-mono text-xs uppercase tracking-[0.16em]">Tear here</span>
        </div>

        <section id="example" aria-labelledby="example-heading">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <SplitHeading id="example-heading" className={heading}>
              An example
            </SplitHeading>
            <Stamp label="Demo data" rotate={-4} />
          </div>
          <p className="mt-3 text-muted">From a synthetic shop. Every figure below comes from a saved run.</p>
          <ul className="mt-8 flex flex-col gap-6">
            {top && (
              <Row
                label={top.title}
                value={`−${formatNaira(top.impact_ngn)}`}
                valueClass="text-accent"
                note={`The largest cause. Profit for the ${demo.frame.days ?? 7} days would have been ${formatNaira(top.counterfactual_ngn)} without it.`}
              />
            )}
            {cash && (
              <Row
                label="Transfers that never reached the bank"
                value={formatNaira(cash.impact_ngn)}
                delay={80}
                note={`${cash.evidence[0].row_ids.length} transfer sales were recorded at the till but never reached the bank. The sales still count toward profit, but this money is missing from your account.`}
              />
            )}
            {demo.ruled_out.map((r, i) => (
              <Reveal as="li" key={r.cause_id} delay={160 + i * 80}>
                <div className="flex items-baseline gap-2 text-muted">
                  <span className="min-w-0">
                    <span className="strike-r font-semibold">{r.hypothesis}</span>
                  </span>
                  <span className="leader" aria-hidden />
                  <span className="shrink-0 font-mono text-sm uppercase">ruled out</span>
                </div>
              </Reveal>
            ))}
          </ul>
          <p className="mt-6 text-muted">Some causes are tested and ruled out, so you do not chase the wrong fix.</p>
        </section>

        <hr className="cut-line my-12 border-0" />

        <section aria-labelledby="limits">
          <SplitHeading id="limits" className={heading}>
            Not included
          </SplitHeading>
          <ul className="mt-8 flex flex-col gap-6">
            <Row label="Guessing a cause" value="never" note="It does not guess a cause without records. If the records do not support it, it says so." />
            <Row label="Moving your money" value="never" delay={80} note="It does not move money or file anything for you. It recommends the next action and you decide." />
          </ul>
        </section>

        <hr className="cut-line my-12 border-0" />

        <Reveal className="flex flex-col items-center gap-6 text-center">
          <p className="font-display text-3xl font-extrabold tracking-tight [font-stretch:120%] sm:text-4xl">Ask about your shop.</p>
          <Link
            href="/investigate"
            className="inline-flex h-12 items-center gap-2 rounded-full bg-ink px-7 font-bold text-paper transition-[background-color,transform] duration-150 hover:bg-accent active:scale-[0.97]"
          >
            Investigate
            <ArrowRightIcon size={18} aria-hidden />
          </Link>
        </Reveal>

        <div className="mt-14 flex flex-col items-center gap-3 text-center font-mono text-xs text-muted">
          <Barcode seed={demo.run_id} />
          <p className="max-w-sm leading-relaxed">
            Built with Zetaris for the shop records, Meterless Nightshift for the model calls, and NVIDIA Nemotron for
            rating the evidence.
          </p>
          <p>Demo shop data is synthetic. No real shop, customer or bank data is used.</p>
          <a href="https://github.com/adr1en360/Becuz#readme" className="font-semibold text-ink underline underline-offset-4 hover:text-accent">
            Read the README
          </a>
        </div>
      </article>
    </div>
  );
}
