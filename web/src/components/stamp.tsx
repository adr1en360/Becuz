"use client";

import type { CSSProperties } from "react";
import { useSeen } from "@/lib/use-seen";

type Props = { label: string; tone?: "ink" | "accent"; rotate?: number };

export function Stamp({ label, tone = "ink", rotate = -5 }: Props) {
  const [ref, seen] = useSeen<HTMLSpanElement>();
  return (
    <span
      ref={ref}
      data-seen={seen}
      className={`stamp ${tone === "accent" ? "text-accent" : "text-ink"}`}
      style={{ "--r": `${rotate}deg` } as CSSProperties}
    >
      {label}
    </span>
  );
}
