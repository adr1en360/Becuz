import { Hero } from "@/components/landing/hero";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingHeader } from "@/components/landing/landing-header";
import { LongReceipt } from "@/components/landing/long-receipt";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col">
      <LandingHeader />
      <main className="flex-1">
        <Hero />
        <LongReceipt />
      </main>
      <LandingFooter />
    </div>
  );
}
