import Link from "next/link";
import { ArrowRightIcon, DatabaseIcon } from "@solar-icons/react/outline";
import { primaryButton, secondaryButton } from "./buttons";
import { HeroReceipt } from "./hero-receipt";

const delay = (ms: number) => ({ "--d": `${ms}ms` }) as React.CSSProperties;
const lines = [
  ["Know", "why", "your"],
  ["profit", "moved."],
];

export function Hero() {
  return (
    <section aria-labelledby="hero" className="mx-auto w-full max-w-5xl px-4 pb-24 pt-24 sm:px-8 lg:pb-32 lg:pt-32">
      <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,27rem)] lg:gap-x-14">
        <div className="flex flex-col gap-7 lg:pt-6">
          <p style={delay(0)} className="rise inline-flex w-fit items-center gap-2 rounded-full border border-desk-line px-3 py-1 text-xs font-semibold text-flare">
            <span className="size-2 rounded-full bg-flare" aria-hidden />
            Track 2, The Agent That Can Explain Why
          </p>

          <div className="hero-title">
            <h1
              id="hero"
              className="font-display text-[3.4rem] font-extrabold leading-[0.88] tracking-[-0.035em] [font-stretch:120%] sm:text-8xl lg:text-[6.5rem] lg:[font-stretch:105%]"
            >
              {lines.map((line, l) => (
                <span key={l} className="block">
                  {line.map((word, w) => (
                    <span key={word}>
                      <span className="mask">
                        <span className={`word ${word === "moved." ? "text-flare" : ""}`} style={delay(80 + (l * 3 + w) * 70)}>
                          {word}
                        </span>
                      </span>{" "}
                    </span>
                  ))}
                </span>
              ))}
            </h1>
          </div>

          <p style={delay(420)} className="rise max-w-md text-lg leading-relaxed text-desk-muted">
            Becuz checks your sales, bank, supplier and expense records and tells you why, with the records behind every
            cause.
          </p>

          <div style={delay(520)} className="rise flex flex-wrap items-center gap-3">
            <Link href="/investigate" className={primaryButton}>
              Investigate
              <ArrowRightIcon size={18} aria-hidden />
            </Link>
            <a href="#how-it-works" className={secondaryButton}>
              See how it works
            </a>
          </div>

          <p style={delay(620)} className="rise flex flex-wrap items-center gap-2 border-t border-desk-line pt-5 font-mono text-xs text-desk-muted">
            <DatabaseIcon size={14} className="text-flare" aria-hidden />
            Zetaris data layer, Meterless Nightshift, NVIDIA Nemotron
          </p>
        </div>

        <div className="hero-receipt mx-auto w-full max-w-[27rem] lg:mx-0">
          <HeroReceipt />
        </div>
      </div>
    </section>
  );
}
