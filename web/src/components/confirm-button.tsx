"use client";

import { useState } from "react";
import { CheckCircleIcon as CheckBold } from "@solar-icons/react/bold";
import { CheckCircleIcon as CheckOutline } from "@solar-icons/react/outline";
import { confirmCause } from "@/lib/api";

type State = { kind: "idle" } | { kind: "saving" } | { kind: "saved" } | { kind: "error"; message: string };

export function ConfirmButton({ runId, causeId }: { runId: string; causeId: string }) {
  const [state, setState] = useState<State>({ kind: "idle" });

  async function confirm() {
    setState({ kind: "saving" });
    try {
      await confirmCause(runId, causeId);
      setState({ kind: "saved" });
    } catch (error) {
      setState({ kind: "error", message: error instanceof Error ? error.message : "Could not save this." });
    }
  }

  if (state.kind === "saved") {
    return (
      <p role="status" className="mt-5 flex items-center gap-2 text-sm font-semibold">
        <CheckBold size={20} className="text-accent" aria-hidden />
        Saved. Becuz will test this cause first next time.
      </p>
    );
  }

  return (
    <div className="mt-5">
      <button
        type="button"
        onClick={confirm}
        disabled={state.kind === "saving"}
        className="inline-flex h-10 cursor-pointer items-center gap-2 rounded-full border-2 border-ink px-4 text-sm font-bold hover:bg-ink hover:text-paper disabled:cursor-wait disabled:opacity-60"
      >
        <CheckOutline size={18} aria-hidden />
        {state.kind === "saving" ? "Saving..." : "This was right"}
      </button>
      {state.kind === "error" && (
        <p role="alert" className="mt-2 text-sm text-accent">
          {state.message}
        </p>
      )}
    </div>
  );
}
