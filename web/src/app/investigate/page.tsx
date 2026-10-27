import { InvestigationApp } from "@/components/investigation-app";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export default function InvestigatePage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <h1 className="sr-only">Becuz investigation</h1>
      <SiteHeader />
      <InvestigationApp />
      <SiteFooter />
    </div>
  );
}
