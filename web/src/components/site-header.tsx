import Link from "next/link";
import { DatabaseIcon } from "@solar-icons/react/outline";

export function SiteHeader() {
  return (
    <header className="flex w-full shrink-0 items-center justify-between border-b border-desk-line px-4 py-4 sm:px-8 print:hidden">
      <Link href="/" aria-label="Becuz home" className="font-display text-2xl font-extrabold tracking-tight [font-stretch:125%]">
        Becuz<span className="text-flare">.</span>
      </Link>
      <span className="inline-flex items-center gap-2 rounded-full border border-desk-line px-3.5 py-1.5 text-sm text-desk-muted">
        <DatabaseIcon size={16} aria-hidden />
        Synthetic data
      </span>
    </header>
  );
}
