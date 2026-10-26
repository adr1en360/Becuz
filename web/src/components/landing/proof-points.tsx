import { Reveal } from "./reveal";

const points = [
  "Every naira figure is computed from records, not guessed by the model.",
  <>A second check <span className="whitespace-nowrap">re-runs</span> the evidence before a cause is shown.</>,
  "Causes you confirm are checked first next time.",
];

export function ProofPoints() {
  return (
    <section aria-label="What you can rely on" className="mx-auto w-full max-w-5xl px-4 pb-24 sm:px-8 lg:pb-32">
      <ul className="grid gap-10 lg:grid-cols-3 lg:gap-12">
        {points.map((text, i) => (
          <Reveal key={i} as="li" delay={i * 90}>
            <span aria-hidden className="block h-1 w-12 rounded-full bg-flare" />
            <p className="mt-5 text-balance font-display text-2xl font-bold leading-tight [font-stretch:105%]">{text}</p>
          </Reveal>
        ))}
      </ul>
    </section>
  );
}
