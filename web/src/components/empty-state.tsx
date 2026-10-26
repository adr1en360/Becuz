import type { ReactNode } from "react";
import { ReportOutline } from "./report-outline";

export function EmptyState({ composer, alert, live }: { composer: ReactNode; alert?: ReactNode; live?: ReactNode }) {
  return (
    <main className="mx-auto grid w-full max-w-5xl flex-1 gap-14 px-4 pb-20 pt-8 sm:px-8 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)] lg:gap-16 lg:pt-14">
      <div className="flex flex-col gap-9">
        <div className="flex flex-col gap-5">
          <h1 className="text-balance font-display text-[2.75rem] font-extrabold leading-[0.95] tracking-[-0.02em] [font-stretch:125%] sm:text-6xl">
            Ask why your profit moved.
          </h1>
          <p className="max-w-md text-lg leading-relaxed text-desk-muted">
            Becuz checks your till, bank, supplier invoices and expenses, and prints the receipts behind every cause.
          </p>
        </div>
        {alert}
        {composer}
      </div>
      <div className="lg:pt-3">
        {live ?? <ReportOutline />}
      </div>
    </main>
  );
}
