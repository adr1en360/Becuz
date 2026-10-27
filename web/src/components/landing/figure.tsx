"use client";

import { CountUp } from "@/components/count-up";
import { formatNaira } from "@/lib/format";
import { useSeen } from "@/lib/use-seen";

const formats = {
  naira: formatNaira,
  percent: (n: number) => n.toFixed(1),
  count: (n: number) => Math.round(n).toLocaleString("en-NG"),
};

// Counts up once, when scrolled into view. The final value is laid out invisibly so the line never changes width.
export function Figure({ value, kind }: { value: number; kind: keyof typeof formats }) {
  const format = formats[kind];
  const [ref, seen] = useSeen<HTMLSpanElement>();
  return (
    <span ref={ref} className="num relative inline-block font-mono font-medium">
      <span aria-hidden className="invisible">
        {format(value)}
      </span>
      <span className="absolute left-0 top-0">
        {seen ? <CountUp value={value} format={format} duration={900} /> : <span className="sr-only">{format(value)}</span>}
      </span>
    </span>
  );
}
