import Link from "next/link";
import { ArrowRightIcon, CloseCircleIcon } from "@solar-icons/react/outline";
import { Backdrop } from "./backdrop";
import { primaryButton } from "./buttons";
import { Reveal } from "./reveal";
import { SplitHeading } from "./split-heading";

const limits = [
  "It does not guess a cause without records. If the records do not support it, it says so.",
  "It does not move money or file anything for you. It recommends the next action and you decide.",
];

export function Closing() {
  return (
    <section aria-labelledby="limits" className="relative isolate overflow-hidden">
      <Backdrop />
      <div className="relative mx-auto w-full max-w-6xl px-4 py-24 sm:px-8 lg:py-32">
        <div className="grid grid-cols-1 gap-14 lg:grid-cols-2 lg:gap-20">
          <div>
            <SplitHeading id="limits" className="text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-5xl">
              What Becuz will not do
            </SplitHeading>
            <ul className="mt-8 flex flex-col gap-5">
              {limits.map((line, i) => (
                <Reveal as="li" key={line} delay={i * 120} from="left" className="flex gap-3 text-lg leading-relaxed">
                  <CloseCircleIcon size={22} className="mt-1 shrink-0 text-flare" aria-hidden />
                  {line}
                </Reveal>
              ))}
            </ul>
          </div>
          <Reveal from="right" className="flex flex-col items-start justify-center gap-6 lg:items-end lg:text-right">
            <p className="font-display text-5xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-6xl">
              Ask about your <span className="text-flare">shop.</span>
            </p>
            <Link href="/investigate" className={primaryButton}>
              Investigate
              <ArrowRightIcon size={18} aria-hidden />
            </Link>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
