import { Composer } from "@/components/composer";
import { ReportOutline } from "@/components/report-outline";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="mx-auto grid w-full max-w-5xl flex-1 gap-12 px-4 pb-16 pt-8 sm:px-8 lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)] lg:gap-20 lg:pt-16">
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-4">
            <h1 className="text-balance text-4xl font-bold leading-[1.05] tracking-[-0.03em] sm:text-5xl">
              Ask why your profit moved.
            </h1>
            <p className="max-w-md text-lg leading-relaxed text-muted">
              Becuz checks your till, bank, supplier invoices and expenses, and shows the records behind every cause.
            </p>
          </div>
          <Composer />
        </div>
        <ReportOutline />
      </main>
      <SiteFooter />
    </div>
  );
}
