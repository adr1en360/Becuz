import { ArrowRightIcon } from "@solar-icons/react/outline";

export function Composer() {
  return (
    <form className="flex flex-col gap-4" aria-describedby="composer-note">
      <label htmlFor="question" className="text-sm font-semibold">
        Your question
      </label>
      <textarea
        id="question"
        name="question"
        rows={3}
        defaultValue="Why is my profit down this week?"
        className="w-full resize-none rounded-2xl border border-rule-strong bg-field px-4 py-3.5 text-lg leading-snug text-ink placeholder:text-muted"
      />
      <div className="flex flex-col items-start gap-3">
        <button
          type="submit"
          disabled
          className="inline-flex h-12 items-center gap-2 rounded-full bg-disabled px-6 text-base font-semibold text-disabled-text disabled:cursor-not-allowed"
        >
          Investigate
          <ArrowRightIcon size={18} aria-hidden />
        </button>
        <p id="composer-note" className="max-w-sm text-sm text-muted">
          The agent is not connected yet. This button works once the server exposes its run endpoint.
        </p>
      </div>
    </form>
  );
}
