import { InvestigationApp } from "@/components/investigation-app";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <InvestigationApp />
      <SiteFooter />
    </div>
  );
}
