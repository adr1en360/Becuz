import { Reveal } from "./reveal";

const steps = [
  "You ask about your week.",
  "Becuz checks your sales, bank, supplier and expense records through Zetaris.",
  "A second check re-runs the evidence for every cause.",
  "You get the causes, the records behind them, the causes ruled out, and one action per cause.",
];

export function HowItWorks() {
  return (
    <section id="how-it-works" aria-labelledby="how" className="mx-auto w-full max-w-5xl px-4 pt-24 sm:px-8 lg:pt-32">
      <Reveal>
        <h2 id="how" className="text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-6xl">
          How it works
        </h2>
      </Reveal>
      <ol className="mt-12 grid gap-10 lg:grid-cols-4 lg:gap-8">
        {steps.map((text, i) => (
          <Reveal key={text} as="li" delay={i * 90} className="flex gap-5 lg:flex-col lg:gap-4">
            <span
              aria-hidden
              className="num font-display text-6xl font-extrabold leading-none text-accent [font-stretch:125%] sm:text-7xl"
            >
              {i + 1}
            </span>
            <p className="text-lg leading-snug lg:border-t-2 lg:border-dashed lg:border-ink/40 lg:pt-4">{text}</p>
          </Reveal>
        ))}
      </ol>
    </section>
  );
}
