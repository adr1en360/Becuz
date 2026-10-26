import { Leader, Receipt, SectionTitle } from "./receipt";

const parts = [
  ["The headline", "Profit this week against your 4-week average, in naira."],
  ["Where it went", "The change split into sales, stock cost, wastage, expenses and money that never reached the bank."],
  ["Each cause, with records", "Its naira effect, the record IDs behind it, what would prove it wrong, and the independent re-check."],
  ["What was ruled out", "Causes that were tested and rejected, and the reason."],
  ["What is not explained", "The part of the change that no cause accounts for, stated plainly."],
  ["What to do this week", "Checks and actions, and the questions only you can answer."],
] as const;

export function ReportOutline() {
  return (
    <Receipt>
      <SectionTitle id="outline-heading">What you get back</SectionTitle>
      <ol className="mt-6 flex flex-col gap-5">
        {parts.map(([title, body]) => (
          <li key={title}>
            <Leader label={title} value="--" valueClass="text-muted" />
            <p className="mt-1 max-w-prose text-sm leading-relaxed text-muted">{body}</p>
          </li>
        ))}
      </ol>
      <p className="mt-8 font-mono text-xs uppercase tracking-[0.16em] text-muted">
        Every figure comes from a query you can read.
      </p>
    </Receipt>
  );
}
