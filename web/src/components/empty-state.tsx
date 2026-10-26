import { ReportOutline } from "./report-outline";

export function EmptyState() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col items-center gap-10 py-6 text-center">
      <div className="flex max-w-xl flex-col items-center gap-3">
        <h2 className="text-balance font-display text-3xl font-extrabold tracking-tight [font-stretch:120%] sm:text-4xl text-paper">
          Ready to investigate your week
        </h2>
        <p className="text-base text-desk-muted leading-relaxed">
          Ask why your profit moved using the box above, or choose an example question. Becuz checks your till sales,
          bank credits, supplier invoices and expense records to find the truth in naira.
        </p>
      </div>

      <div className="w-full max-w-md text-left">
        <ReportOutline />
      </div>
    </div>
  );
}
