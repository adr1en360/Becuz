"use client";

import { CountUp } from "@/components/count-up";
import { formatNaira } from "@/lib/format";

const formats = { naira: formatNaira, percent: (n: number) => n.toFixed(1) };

// The final value is laid out invisibly so the count-up never changes the width of the line.
export function Figure({ value, kind }: { value: number; kind: keyof typeof formats }) {
  const format = formats[kind];
  return (
    <span className="num relative inline-block font-mono font-medium">
      <span aria-hidden className="invisible">
        {format(value)}
      </span>
      <span className="absolute left-0 top-0">
        <CountUp value={value} format={format} duration={900} />
      </span>
    </span>
  );
}
