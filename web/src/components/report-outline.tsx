import type { ComponentType, SVGProps } from "react";
import {
  BillListIcon,
  BranchingPathsDownIcon,
  ChecklistMinimalisticIcon,
  CloseCircleIcon,
  QuestionCircleIcon,
  ShieldCheckIcon,
} from "@solar-icons/react/outline";

type Icon = ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>;

const parts: { icon: Icon; title: string; body: string }[] = [
  {
    icon: BillListIcon,
    title: "The headline",
    body: "Profit this week against your 4-week average, in naira.",
  },
  {
    icon: BranchingPathsDownIcon,
    title: "Where it went",
    body: "The change split into sales, stock cost, wastage, expenses and money that never reached the bank.",
  },
  {
    icon: ShieldCheckIcon,
    title: "Each cause, with its records",
    body: "Its naira effect, the record IDs behind it, what would prove it wrong, and the independent re-check.",
  },
  {
    icon: CloseCircleIcon,
    title: "What was ruled out",
    body: "Causes that were tested and rejected, and the reason.",
  },
  {
    icon: QuestionCircleIcon,
    title: "What is not explained",
    body: "The part of the change that no cause accounts for, stated plainly.",
  },
  {
    icon: ChecklistMinimalisticIcon,
    title: "What to do this week",
    body: "Checks and actions, and the questions only you can answer.",
  },
];

export function ReportOutline() {
  return (
    <section aria-labelledby="outline-heading">
      <h2 id="outline-heading" className="text-lg font-semibold">
        What you get back
      </h2>
      <ol className="mt-4 border-b border-rule-strong">
        {parts.map(({ icon: Icon, title, body }, i) => (
          <li
            key={title}
            className="ledger-row relative flex gap-4 py-5"
            style={{ "--i": i } as React.CSSProperties}
          >
            <Icon size={22} className="mt-0.5 shrink-0 text-ink" aria-hidden />
            <div>
              <h3 className="text-base font-semibold">{title}</h3>
              <p className="mt-1 max-w-prose text-muted">{body}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
