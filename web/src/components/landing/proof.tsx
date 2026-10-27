import Link from "next/link";
import { ArrowRightIcon } from "@solar-icons/react/outline";
import { demo } from "@/lib/demo-report";
import { HeroReceipt } from "./hero-receipt";
import { Reveal } from "./reveal";
import { SplitHeading } from "./split-heading";

const top = demo.causes[0];
const cash = demo.cash_gaps?.[0];

export function Proof() {
  return (
    <section id="example" aria-labelledby="example-heading" className="relative overflow-hidden bg-desk-2 py-24 lg:py-32">
      <div className="mx-auto grid w-full max-w-6xl grid-cols-1 items-center gap-14 px-4 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,27rem)] lg:gap-20">
        <div>
          <SplitHeading id="example-heading" className="max-w-xl text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-6xl">
            A receipt for every answer
          </SplitHeading>
          <Reveal delay={120}>
            <p className="mt-6 max-w-lg text-lg leading-relaxed text-desk-muted">
              Every cause prints with its naira effect, the records behind it and a second check. Watch it print for the
              example shop.
            </p>
          </Reveal>
          <ul className="mt-10 flex flex-col gap-6">
            {top && (
              <Reveal as="li" from="left" delay={160}>
                <p className="font-display text-2xl font-bold leading-tight [font-stretch:110%]">{top.title}.</p>
                <p className="mt-1 text-desk-muted">
                  The largest cause, found in {top.evidence[0].row_ids.length} supplier records.
                </p>
              </Reveal>
            )}
            {cash && (
              <Reveal as="li" from="left" delay={260}>
                <p className="font-display text-2xl font-bold leading-tight [font-stretch:110%]">Missing money, kept apart.</p>
                <p className="mt-1 text-desk-muted">
                  {cash.evidence[0].row_ids.length} transfer sales were recorded at the till but never reached the bank. They
                  still count as profit, but the cash is missing.
                </p>
              </Reveal>
            )}
            <Reveal as="li" from="left" delay={360}>
              <p className="font-display text-2xl font-bold leading-tight [font-stretch:110%]">Wrong guesses, struck out.</p>
              <p className="mt-1 text-desk-muted">Causes that were tested and ruled out, so you do not chase the wrong fix.</p>
            </Reveal>
          </ul>
          <Reveal delay={420}>
            <Link
              href="/investigate"
              className="mt-10 inline-flex h-12 items-center gap-2 rounded-full bg-paper px-6 font-bold text-ink transition-[background-color,transform] duration-150 hover:bg-flare active:scale-[0.97]"
            >
              Try it yourself
              <ArrowRightIcon size={18} aria-hidden />
            </Link>
          </Reveal>
        </div>
        <div className="mx-auto w-full max-w-[27rem]">
          <HeroReceipt />
        </div>
      </div>
    </section>
  );
}
