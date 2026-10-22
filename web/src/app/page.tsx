import { DevBanner } from "@/components/dev-banner";
import { EmptyState } from "@/components/empty-state";
import { Report } from "@/components/report";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { loadInvestigation } from "@/lib/investigation-source";

export default async function Home() {
  const investigation = await loadInvestigation();
  return (
    <div className="flex min-h-dvh flex-col">
      {investigation && <DevBanner />}
      <SiteHeader />
      {investigation ? <Report data={investigation} /> : <EmptyState />}
      <SiteFooter />
    </div>
  );
}
