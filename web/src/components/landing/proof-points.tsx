import { Reveal } from "./reveal";
import { DatabaseIcon, LayersIcon, ShieldCheckIcon } from "@solar-icons/react/outline";

const points = [
  {
    icon: DatabaseIcon,
    title: "SQL computes, model rates",
    text: "Every naira figure is computed from records by SQL, not generated or guessed by an LLM.",
  },
  {
    icon: ShieldCheckIcon,
    title: "Independent verification",
    text: "A second check re-runs every query before a cause is supported. Weak claims are rejected.",
  },
  {
    icon: LayersIcon,
    title: "Confirmed memory",
    text: "Causes you confirm are remembered in H-MEM and tested first in your next investigation.",
  },
];

export function ProofPoints() {
  return (
    <section aria-label="What you can rely on" className="mx-auto w-full max-w-5xl px-4 pb-20 sm:px-8 lg:pb-28">
      <ul className="grid gap-6 sm:grid-cols-3">
        {points.map((pt, i) => {
          const Icon = pt.icon;
          return (
            <Reveal
              key={pt.title}
              as="li"
              delay={i * 90}
              className="lift rounded-3xl border border-desk-line bg-desk-2/60 p-6 flex flex-col justify-between gap-4"
            >
              <div>
                <div className="flex size-10 items-center justify-center rounded-full bg-desk border border-desk-line/70 text-flare">
                  <Icon size={20} aria-hidden />
                </div>
                <h3 className="mt-4 font-display text-xl font-bold text-paper [font-stretch:115%]">
                  {pt.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-desk-muted">
                  {pt.text}
                </p>
              </div>
            </Reveal>
          );
        })}
      </ul>
    </section>
  );
}
