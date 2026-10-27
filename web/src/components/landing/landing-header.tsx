import Link from "next/link";
import { smallPrimaryButton } from "./buttons";

export function LandingHeader() {
  return (
    <header className="landing-header fixed inset-x-0 top-0 z-40 border-b border-desk-line bg-desk">
      <div aria-hidden className="progress absolute inset-x-0 -bottom-px h-[3px] origin-left scale-x-0 bg-flare" />
      <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between gap-3 px-4 sm:px-8">
        <Link href="/" aria-label="Becuz home" className="font-display text-2xl font-extrabold tracking-tight [font-stretch:125%]">
          Becuz<span className="text-flare">.</span>
        </Link>
        <nav aria-label="Main" className="flex items-center gap-2.5 sm:gap-6">
          <a href="#how-it-works" className="whitespace-nowrap text-sm font-semibold text-desk-muted hover:text-paper sm:text-base transition-colors">
            How it works
          </a>
          <a href="#example" className="hidden whitespace-nowrap text-sm font-semibold text-desk-muted hover:text-paper sm:inline transition-colors">
            Example
          </a>
          <Link href="/investigate" className={smallPrimaryButton}>
            Investigate
          </Link>
        </nav>
      </div>
    </header>
  );
}
