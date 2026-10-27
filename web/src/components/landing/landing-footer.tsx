export function LandingFooter() {
  return (
    <footer className="border-t border-desk-line">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-10 text-sm text-desk-muted sm:px-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex flex-col gap-2">
          <span className="font-display text-2xl font-extrabold tracking-tight text-paper [font-stretch:125%]">
            Becuz<span className="text-flare">.</span>
          </span>
          <p className="max-w-md">
            Built with Zetaris for the shop records, Meterless Nightshift for the model calls, and NVIDIA Nemotron for
            rating the evidence.
          </p>
        </div>
        <div className="flex flex-col gap-2 lg:items-end lg:text-right">
          <p>Demo shop data is synthetic. No real shop, customer or bank data is used.</p>
          <p>Findings show correlation, not proven causation.</p>
          <a href="https://github.com/adr1en360/Becuz#readme" className="font-semibold text-paper underline underline-offset-4 hover:text-flare">
            Read the README
          </a>
        </div>
      </div>
    </footer>
  );
}
