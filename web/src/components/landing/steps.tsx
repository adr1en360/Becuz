import { DatabaseIcon, DocumentTextIcon, LayersIcon, ShieldCheckIcon } from "@solar-icons/react/outline";
import { demo } from "@/lib/demo-report";
import { Reveal } from "./reveal";
import { SplitHeading } from "./split-heading";

const STEPS = [
  {
    title: "You ask",
    by: "Meterless Scout Intent",
    icon: DocumentTextIcon,
    body: `Ask about your shop's money for any 1 to 28 days. Becuz scopes the question, limits which records it may read, and compares the period with ${demo.frame.baseline ?? "the periods before"}.`,
  },
  {
    title: "It reads your records",
    by: "Zetaris",
    icon: DatabaseIcon,
    body: "Till sales, the bank statement, supplier invoices and the expense book are queried where they live. Becuz can read them, never change them.",
  },
  {
    title: "It checks twice",
    by: "Nightshift and NVIDIA Nemotron",
    icon: ShieldCheckIcon,
    body: "A second agent re-runs every query. A claim whose numbers do not match is sent back or ruled out, and Nemotron rates how strong the evidence is.",
  },
  {
    title: "You get the receipt",
    by: "H-MEM memory",
    icon: LayersIcon,
    body: "Each cause with its naira effect and the records behind it, what was ruled out, and one action per cause. Causes you confirm are checked first next time.",
  },
];

// Steps slide in from alternating sides along a line that fills as you scroll.
export function Steps() {
  return (
    <section id="how-it-works" aria-labelledby="how-heading" className="mx-auto w-full max-w-6xl px-4 py-24 sm:px-8 lg:py-32">
      <SplitHeading id="how-heading" className="max-w-3xl text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-6xl">
        How it works
      </SplitHeading>

      <ol className="relative mt-16 flex flex-col gap-14 lg:gap-6">
        <span aria-hidden className="absolute bottom-0 left-5 top-0 w-0.5 rounded-full bg-desk-line lg:left-1/2 lg:-translate-x-1/2">
          <span className="rail-fill block h-full w-full origin-top rounded-full bg-flare" />
        </span>
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          const right = i % 2 === 1;
          return (
            <li key={step.title} className="relative grid gap-6 pl-16 lg:grid-cols-2 lg:gap-24 lg:pl-0">
              <span className="absolute left-0 top-0 z-10 flex size-10 items-center justify-center rounded-full border-2 border-flare bg-desk text-flare lg:left-1/2 lg:-translate-x-1/2">
                <Icon size={18} aria-hidden />
              </span>
              <Reveal from={right ? "right" : "left"} className={right ? "lg:col-start-2" : "lg:text-right"}>
                <p className="outline-num font-display text-7xl font-extrabold leading-none [font-stretch:125%] sm:text-8xl" aria-hidden>
                  {i + 1}
                </p>
                <h3 className="mt-3 font-display text-3xl font-bold leading-tight [font-stretch:110%]">{step.title}</h3>
                <p className={`mt-3 max-w-md leading-relaxed text-desk-muted ${right ? "" : "lg:ml-auto"}`}>{step.body}</p>
                <p className="mt-4 font-mono text-xs uppercase tracking-[0.16em] text-flare">{step.by}</p>
              </Reveal>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
