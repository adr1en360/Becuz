import Link from "next/link";
import { ArrowRightIcon } from "@solar-icons/react/outline";
import { Stamp } from "@/components/stamp";
import { primaryButton, secondaryButton } from "./buttons";
import { Figure } from "./figure";

const delay = (ms: number) => ({ "--d": `${ms}ms` }) as React.CSSProperties;

export function Hero() {
  return (
    <section aria-labelledby="hero" className="mx-auto w-full max-w-5xl px-4 pb-20 pt-28 sm:px-8 lg:pb-32 lg:pt-36">
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,27rem)] lg:gap-x-14 lg:gap-y-8">
        <h1
          id="hero"
          style={delay(0)}
          className="rise text-balance font-display text-[3rem] font-extrabold leading-[0.9] tracking-[-0.03em] [font-stretch:125%] sm:text-7xl lg:col-start-1 lg:row-start-1 lg:text-[4.25rem]"
        >
          Know why your profit moved this week.
        </h1>

        <div className="mx-auto w-full max-w-[27rem] lg:col-start-2 lg:row-span-3 lg:row-start-1 lg:mx-0 lg:self-start lg:rotate-[1.5deg]">
          <div aria-hidden className="relative z-10 h-4 rounded-full border border-desk-line bg-desk-2" />
          <div
            style={delay(150)}
            className="receipt slot paper print-fast relative -mt-2 px-6 pb-10 pt-9 sm:px-8"
          >
            <div className="flex flex-wrap items-center gap-3">
              <Stamp label="Demo data" rotate={-3} />
              <p className="font-mono text-xs text-muted">Synthetic demo shop</p>
            </div>
            <p className="mt-7 text-2xl leading-snug sm:text-[1.75rem]">
              <span className="block">
                This week, profit was{" "}
                <span className="whitespace-nowrap">
                  <Figure value={241717} kind="naira" />.
                </span>
              </span>
              <span className="mt-3 block">
                A usual week is{" "}
                <span className="whitespace-nowrap">
                  <Figure value={379412} kind="naira" />.
                </span>
              </span>
              <span className="cut-line mt-6 block pt-6 font-bold text-accent">
                That is <Figure value={137695} kind="naira" /> less, down{" "}
                <span className="whitespace-nowrap">
                  <Figure value={36.3} kind="percent" /> percent.
                </span>
              </span>
            </p>
          </div>
        </div>

        <p style={delay(150)} className="rise max-w-md text-lg leading-relaxed text-desk-muted lg:col-start-1 lg:row-start-2">
          Becuz checks your sales, bank, supplier and expense records and tells you why, with the records behind every cause.
        </p>

        <div style={delay(350)} className="rise flex flex-wrap gap-3 lg:col-start-1 lg:row-start-3">
          <Link href="/investigate" className={primaryButton}>
            Investigate
            <ArrowRightIcon size={18} aria-hidden />
          </Link>
          <a href="#how-it-works" className={secondaryButton}>
            See how it works
          </a>
        </div>
      </div>
    </section>
  );
}
