import Link from "next/link";
import { ArrowRightIcon, ArrowRightUpIcon, DatabaseIcon, ShieldCheckIcon } from "@solar-icons/react/outline";
import { primaryButton } from "./buttons";

export function LandingFooter() {
  return (
    <footer className="border-t border-desk-line bg-desk pt-16 pb-12 text-desk-muted">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-14 px-4 sm:px-8">
        {/* Pre-footer CTA */}
        <div className="flex flex-col items-start justify-between gap-6 rounded-3xl border border-desk-line bg-desk-2/70 p-8 sm:flex-row sm:items-center sm:p-10">
          <div className="max-w-xl">
            <h3 className="font-display text-2xl font-extrabold text-paper [font-stretch:115%] sm:text-3xl">
              Ready to see where your money went?
            </h3>
            <p className="mt-2 text-sm text-desk-muted sm:text-base leading-relaxed">
              Run an investigation in sample mode or against your live records. Zero mocked answers: every naira
              figure comes from SQL.
            </p>
          </div>
          <Link href="/investigate" className={`${primaryButton} shrink-0`}>
            Investigate now
            <ArrowRightIcon size={18} aria-hidden />
          </Link>
        </div>

        {/* 3-column navigation & architectural disclosure */}
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4 lg:gap-8 text-sm">
          {/* Brand & mission */}
          <div className="flex flex-col gap-3 lg:col-span-1">
            <Link
              href="/"
              aria-label="Becuz home"
              className="font-display text-2xl font-extrabold tracking-tight text-paper [font-stretch:125%]"
            >
              Becuz<span className="text-flare">.</span>
            </Link>
            <p className="text-xs leading-relaxed text-desk-muted">
              Why did my profit move this week? An answer in naira, with a receipt for every claim.
            </p>
            <div className="mt-2 flex flex-col gap-1.5 font-mono text-[11px]">
              <span className="inline-flex items-center gap-1.5 text-paper">
                <ShieldCheckIcon size={14} className="text-flare" aria-hidden />
                Track 2 · Explain Why
              </span>
              <span>Open Agent Hackathon 2026</span>
            </div>
          </div>

          {/* Sponsor technology */}
          <div className="flex flex-col gap-2.5 lg:col-span-2">
            <h4 className="font-mono text-xs uppercase tracking-wider text-paper">Sponsor Architecture</h4>
            <ul className="flex flex-col gap-2 text-xs leading-relaxed">
              <li>
                <span className="font-semibold text-paper">Zetaris Data Layer: </span>
                Four messy S3 sources queried in place through Lightning databases and the Unified Semantic Layer (`becuz`).
              </li>
              <li>
                <span className="font-semibold text-paper">Meterless Engines: </span>
                Scout Intent (signed contract), H-MEM (owner memory), World Model (claims ledger), and Markovian (checker chain).
              </li>
              <li>
                <span className="font-semibold text-paper">Meterless Nightshift & NVIDIA: </span>
                Primary AI provider routing Checker verdicts to NVIDIA Nemotron 3.5 Lightning 30B with signed receipts.
              </li>
            </ul>
          </div>

          {/* Navigation & Links */}
          <div className="flex flex-col gap-2.5">
            <h4 className="font-mono text-xs uppercase tracking-wider text-paper">Navigation</h4>
            <ul className="flex flex-col gap-2 text-xs">
              <li>
                <Link href="/investigate" className="hover:text-paper transition-colors">
                  Run investigation
                </Link>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-paper transition-colors">
                  How it works
                </a>
              </li>
              <li>
                <a href="#example" className="hover:text-paper transition-colors">
                  Sample receipt
                </a>
              </li>
              <li>
                <a href="#limits" className="hover:text-paper transition-colors">
                  What Becuz does not do
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/adr1en360/Becuz"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-paper transition-colors"
                >
                  GitHub repository
                  <ArrowRightUpIcon size={12} aria-hidden />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom copyright and data hygiene disclosure */}
        <div className="flex flex-col gap-3 border-t border-desk-line/50 pt-8 text-xs text-desk-muted sm:flex-row sm:items-center sm:justify-between">
          <p className="flex items-center gap-1.5">
            <DatabaseIcon size={14} aria-hidden />
            Demo data is synthetic. No real shop, customer, or personal bank data is used.
          </p>
          <p>Open source MIT · Team of 2 (Adrien & tmb)</p>
        </div>
      </div>
    </footer>
  );
}
