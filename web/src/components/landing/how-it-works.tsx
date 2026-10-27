"use client";

import { useState } from "react";
import { Reveal } from "./reveal";
import {
  DatabaseIcon,
  DocumentTextIcon,
  LayersIcon,
  ShieldCheckIcon,
} from "@solar-icons/react/outline";

const STAGES = [
  {
    step: "01",
    title: "Detect & Scope",
    lead: "Scout Intent signs the contract",
    body: "Turns your question into a signed investigation contract with strict table boundaries and query budgets, then measures profit against the 4 baseline weeks.",
    sponsor: "Scout Intent Engine",
    icon: DocumentTextIcon,
    code: "Contract #001a17 · profit.explain_change",
  },
  {
    step: "02",
    title: "Query in Place",
    lead: "Zetaris joins your records",
    body: "Queries till sales, bank statement, supplier invoices and expense book in place through Lightning SQL. The agent reads the Unified Semantic Layer as a non-admin.",
    sponsor: "Zetaris Data Layer",
    icon: DatabaseIcon,
    code: "SELECT * FROM becuz.transfer_check",
  },
  {
    step: "03",
    title: "Verify & Judge",
    lead: "Checker re-runs every query",
    body: "The Checker does not trust claims: it independently re-runs the SQL. Mismatches are rejected or sent back, and NVIDIA Nemotron 3.5 Lightning rates evidence credibility.",
    sponsor: "NVIDIA Nemotron · Nightshift",
    icon: ShieldCheckIcon,
    code: "Verdict: MATCH (46,992 NGN from 1 record)",
  },
  {
    step: "04",
    title: "Receipts & Memory",
    lead: "Answers in naira, missing cash separate",
    body: "Prints receipts behind every cause, separates missing cash from profit, rules out red herrings, and stores confirmed causes in H-MEM to check first next time.",
    sponsor: "H-MEM Memory · World Model",
    icon: LayersIcon,
    code: "4 causes verified · ₦28,360 cash gap separated",
  },
] as const;

export function HowItWorks() {
  const [activeStage, setActiveStage] = useState<number>(0);

  return (
    <section
      id="how-it-works"
      aria-labelledby="how-heading"
      className="mx-auto w-full max-w-5xl px-4 py-20 sm:px-8 lg:py-28"
    >
      <Reveal className="flex flex-col gap-4 text-center sm:text-left">
        <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
          <span className="rounded-full border border-desk-line bg-desk-2 px-3 py-1 font-mono text-xs font-semibold text-flare">
            Detect to Act Pipeline
          </span>
        </div>
        <h2
          id="how-heading"
          className="text-balance font-display text-3xl font-extrabold tracking-tight text-paper [font-stretch:125%] sm:text-5xl"
        >
          How Becuz finds the truth
        </h2>
        <p className="max-w-2xl text-base text-desk-muted sm:text-lg leading-relaxed">
          Four coordinated stages. Every naira figure is computed by SQL from your records, and every claim is
          independently re-checked before reaching the receipt.
        </p>
      </Reveal>

      {/* Connecting pipeline flow line */}
      <div className="relative mt-12 hidden lg:block">
        <div className="flow-line h-1 w-full rounded-full opacity-60" aria-hidden />
      </div>

      {/* Stage cards grid */}
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isSelected = activeStage === idx;

          return (
            <Reveal
              key={stage.step}
              delay={idx * 110}
              className={`lift group relative flex cursor-pointer flex-col justify-between rounded-3xl border p-5 transition-all duration-200 ${
                isSelected
                  ? "border-flare bg-desk-2/95 shadow-lg shadow-flare/5"
                  : "border-desk-line bg-desk-2/60 hover:border-paper/40"
              }`}
            >
              <div
                onClick={() => setActiveStage(idx)}
                className="flex flex-col gap-4"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-flare tracking-widest">
                    {stage.step}
                  </span>
                  <div
                    className={`flex size-9 items-center justify-center rounded-full transition-colors ${
                      isSelected
                        ? "bg-flare text-desk"
                        : "bg-desk text-desk-muted group-hover:text-paper"
                    }`}
                  >
                    <Icon size={18} aria-hidden />
                  </div>
                </div>

                <div>
                  <h3 className="font-mono text-xs uppercase tracking-wider text-desk-muted">
                    {stage.title}
                  </h3>
                  <p className="mt-1 font-display text-lg font-bold text-paper [font-stretch:110%]">
                    {stage.lead}
                  </p>
                </div>

                <p className="text-xs leading-relaxed text-desk-muted">
                  {stage.body}
                </p>
              </div>

              <div className="mt-5 border-t border-desk-line/60 pt-3">
                <span className="inline-block rounded-full bg-desk px-2.5 py-1 font-mono text-[10px] font-semibold text-flare">
                  {stage.sponsor}
                </span>
                <p className="mt-2 truncate font-mono text-[11px] text-paper/70">
                  {stage.code}
                </p>
              </div>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
