import { ExampleInvestigation } from "@/components/landing/example-investigation";
import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingHeader } from "@/components/landing/landing-header";
import { Limits } from "@/components/landing/limits";
import { ProofPoints } from "@/components/landing/proof-points";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col">
      <LandingHeader />
      <main className="flex-1">
        <Hero />
        <ProofPoints />
        <HowItWorks />
        <div className="receipt paper my-12 pb-24 pt-20 lg:pb-32 lg:pt-28">
          <ExampleInvestigation />
        </div>
        <Limits />
      </main>
      <LandingFooter />
    </div>
  );
}
