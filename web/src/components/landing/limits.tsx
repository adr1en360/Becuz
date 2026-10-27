import { Reveal } from "./reveal";

export function Limits() {
  return (
    <section aria-labelledby="limits" className="mx-auto w-full max-w-5xl px-4 py-24 sm:px-8 lg:py-32">
      <Reveal>
        <h2 id="limits" className="text-balance font-display text-4xl font-extrabold leading-[0.95] tracking-tight [font-stretch:125%] sm:text-6xl">
          What Becuz does not do
        </h2>
      </Reveal>
      <ul className="mt-10 grid gap-6 lg:grid-cols-2 lg:gap-10">
        {[
          "It does not guess a cause without records. If the records do not support it, it says so.",
          "It does not move money or file anything for you. It recommends the next action and you decide.",
        ].map((text, i) => (
          <Reveal key={text} as="li" delay={i * 70} className="rounded-2xl border-2 border-dashed border-desk-line p-6 sm:p-8">
            <p className="text-balance text-xl leading-snug sm:text-2xl">{text}</p>
          </Reveal>
        ))}
      </ul>
    </section>
  );
}
