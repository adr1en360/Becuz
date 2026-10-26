import Link from "next/link";
import { primaryButton } from "./buttons";

export function LandingHeader() {
  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-desk-line bg-desk">
      <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between gap-3 px-4 sm:px-8">
        <Link href="/" aria-label="Becuz home" className="font-display text-2xl font-extrabold tracking-tight [font-stretch:125%]">
          Becuz<span className="text-flare">.</span>
        </Link>
        <nav aria-label="Main" className="flex items-center gap-3 sm:gap-6">
          <a href="#how-it-works" className="whitespace-nowrap text-sm font-semibold text-desk-muted hover:text-paper sm:text-base">
            <span className="sm:hidden">How it works</span>
            <span className="hidden sm:inline">See how it works</span>
          </a>
          <Link href="/investigate" className={`${primaryButton} h-10 px-5 text-sm sm:text-base`}>
            Investigate
          </Link>
        </nav>
      </div>
    </header>
  );
}
