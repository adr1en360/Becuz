export function LandingFooter() {
  return (
    <footer className="mx-auto w-full max-w-5xl border-t border-desk-line px-4 py-8 text-sm text-desk-muted sm:px-8">
      <p className="max-w-2xl">
        Built with Zetaris for the shop records, Meterless Nightshift for the model calls, and NVIDIA Nemotron for
        rating the evidence.
      </p>
      <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p>Demo shop data is synthetic. No real shop, customer or bank data is used.</p>
        <a
          href="https://github.com/adr1en360/Becuz#readme"
          className="font-semibold text-paper underline decoration-desk-line underline-offset-4 hover:decoration-paper"
        >
          Read the README
        </a>
      </div>
    </footer>
  );
}
