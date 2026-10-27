import { InvestigationApp } from "@/components/investigation-app";
import { SiteHeader } from "@/components/site-header";

export default function InvestigatePage() {
  return (
    <div className="flex min-h-dvh flex-col lg:h-dvh lg:overflow-hidden">
      <SiteHeader />
      <InvestigationApp />
    </div>
  );
}
