import Link from "next/link";
import { ArrowRightIcon, DatabaseIcon } from "@solar-icons/react/outline";
import { Stamp } from "@/components/stamp";
import { primaryButton, secondaryButton } from "./buttons";
import { Figure } from "./figure";
import { HeroBars } from "./hero-bars";
import { Tilt } from "./tilt";

const delay = (ms: number) => ({ "--d": `${ms}ms` }) as React.CSSProperties;
const words = ["Know", "why", "your", "profit", "moved", "this", "week."];

const EXAMPLE_PROMPTS = [
  "Why is my profit down?",
  "Where did my money go?",
  "How is my shop doing?",
] as const;

export function Hero() {
  return (
    <section aria-labelledby="hero" className="mx-auto w-full max-w-5xl px-4 pb-20 pt-24 sm:px-8 lg:pb-28 lg:pt-32">
      <div className="grid gap-10 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,28rem)] lg:gap-x-12 lg:gap-y-8">
        {/* Left Column: Heading, description, and CTAs */}
        <div className="flex flex-col gap-6 lg:col-start-1 lg:row-start-1">
          <div style={delay(50)} className="rise flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-desk-line bg-desk-2/80 px-3 py-1 text-xs font-semibold text-flare">
              <span className="size-2 rounded-full bg-flare animate-pulse" aria-hidden />
              Track 2 · The Agent That Can Explain Why
            </span>
          </div>

          <div className="hero-title">
            <h1
              id="hero"
              className="text-balance font-display text-[2.85rem] font-extrabold leading-[0.93] tracking-[-0.03em] [font-stretch:120%] sm:text-7xl lg:text-[4.25rem] lg:[font-stretch:112%]"
            >
              {words.map((word, i) => (
                <span key={word}>
                  <span className="mask">
                    <span className="word" style={delay(i * 55)}>
                      {word}
                    </span>
                  </span>{" "}
                </span>
              ))}
            </h1>
          </div>

          <p style={delay(160)} className="rise max-w-lg text-lg leading-relaxed text-desk-muted">
            Becuz joins your POS till, bank statement, supplier invoices and expense records to explain profit drops
            in naira, with the verified receipts behind every cause.
          </p>

          <div style={delay(260)} className="rise flex flex-wrap items-center gap-3">
            <Link href="/investigate" className={primaryButton}>
              Investigate
              <ArrowRightIcon size={18} aria-hidden />
            </Link>
            <a href="#how-it-works" className={secondaryButton}>
              See how it works
            </a>
          </div>

          {/* Quick example chips */}
          <div style={delay(340)} className="rise flex flex-wrap items-center gap-2 pt-1 text-xs text-desk-muted">
            <span>Try:</span>
            {EXAMPLE_PROMPTS.map((prompt) => (
              <Link
                key={prompt}
                href="/investigate"
                className="rounded-full border border-desk-line bg-desk-2/60 px-3 py-1 text-xs text-desk-muted transition-colors hover:border-flare hover:text-paper active:scale-95"
              >
                {prompt}
              </Link>
            ))}
          </div>

          {/* Sponsor attribution */}
          <div style={delay(400)} className="rise flex flex-wrap items-center gap-2 border-t border-desk-line/50 pt-5 text-xs font-mono text-desk-muted">
            <DatabaseIcon size={14} className="text-flare" aria-hidden />
            <span>Zetaris data layer · Meterless Nightshift · NVIDIA Nemotron</span>
          </div>
        </div>

        {/* Right Column: Interactive tilted receipt with s01 sample figures */}
        <div className="hero-receipt mx-auto w-full max-w-[28rem] lg:col-start-2 lg:row-start-1 lg:mx-0 lg:self-start">
          <Tilt className="relative">
            <div
              aria-hidden
              className="absolute inset-x-3 top-6 bottom-[-14px] -rotate-[3deg] rounded-sm bg-paper/20 lg:-left-3"
            />
            <div aria-hidden className="relative z-10 h-4 rounded-full border border-desk-line bg-desk-2" />
            <div style={delay(150)} className="receipt slot paper print-fast relative -mt-2 px-6 pb-8 pt-8 sm:px-7">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Stamp label="Demo data" rotate={-2} />
                <p className="font-mono text-xs text-muted">Synthetic shop · s01</p>
              </div>

              <div className="mt-6 text-xl leading-snug sm:text-2xl">
                <span className="block text-ink">
                  This week, profit was{" "}
                  <span className="whitespace-nowrap font-bold">
                    <Figure value={241717} kind="naira" />.
                  </span>
                </span>
                <span className="mt-2 block text-sm text-muted">
                  A usual week is{" "}
                  <span className="whitespace-nowrap font-semibold text-ink">
                    <Figure value={379412} kind="naira" />.
                  </span>
                </span>
                <span className="cut-line mt-4 block pt-4 font-bold text-accent text-lg sm:text-xl">
                  Down <Figure value={137695} kind="naira" /> (
                  <Figure value={36.3} kind="percent" />)
                </span>
              </div>

              <HeroBars />

              {/* Concrete cause breakdown registered in s01 figures */}
              <dl className="mt-5 flex flex-col gap-2 border-t border-dashed border-ink/30 pt-4 font-mono text-xs">
                <div className="flex items-baseline justify-between gap-2">
                  <dt className="text-muted">Supplier raised unit cost</dt>
                  <dd className="num font-bold text-accent">−₦46,992</dd>
                </div>
                <div className="flex items-baseline justify-between gap-2">
                  <dt className="text-muted">Transfers missing from bank</dt>
                  <dd className="num font-bold text-accent">−₦28,360</dd>
                </div>
                <div className="flex items-baseline justify-between gap-2">
                  <dt className="text-muted">POS card fee rise</dt>
                  <dd className="font-semibold text-ink line-through decoration-accent">Ruled out</dd>
                </div>
              </dl>

              <p className="mt-4 font-mono text-[11px] text-muted text-center border-t border-rule/50 pt-2.5">
                Every claim backed by an independent SQL re-check.
              </p>
            </div>
          </Tilt>
        </div>
      </div>
    </section>
  );
}
