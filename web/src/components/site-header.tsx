import { DatabaseIcon } from "@solar-icons/react/outline";

export function SiteHeader() {
  return (
    <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-5 sm:px-8">
      <span className="text-xl font-bold tracking-tight">
        Becuz<span className="text-accent">.</span>
      </span>
      <span className="inline-flex items-center gap-2 rounded-full border border-rule-strong px-3.5 py-1.5 text-sm text-muted">
        <DatabaseIcon size={16} aria-hidden />
        Synthetic data
      </span>
    </header>
  );
}
