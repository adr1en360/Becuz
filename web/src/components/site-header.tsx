import { DatabaseIcon } from "@solar-icons/react/outline";

export function SiteHeader() {
  return (
    <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-5 sm:px-8">
      <span className="font-display text-2xl font-extrabold tracking-tight [font-stretch:125%]">
        Becuz<span className="text-flare">.</span>
      </span>
      <span className="inline-flex items-center gap-2 rounded-full border border-desk-line px-3.5 py-1.5 text-sm text-desk-muted">
        <DatabaseIcon size={16} aria-hidden />
        Synthetic data
      </span>
    </header>
  );
}
