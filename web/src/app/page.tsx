import { Closing } from "@/components/landing/closing";
import { Hero } from "@/components/landing/hero";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingHeader } from "@/components/landing/landing-header";
import { Numbers } from "@/components/landing/numbers";
import { Proof } from "@/components/landing/proof";
import { RecordsTicker } from "@/components/landing/records-ticker";
import { Steps } from "@/components/landing/steps";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col">
      <LandingHeader />
      <main className="flex-1">
        <Hero />
        <RecordsTicker />
        <Numbers />
        <Steps />
        <Proof />
        <Closing />
      </main>
      <LandingFooter />
    </div>
  );
}
