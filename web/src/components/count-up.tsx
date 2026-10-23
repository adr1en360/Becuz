"use client";

import { useEffect, useState } from "react";

type Props = { value: number; format: (n: number) => string; duration?: number };

export function CountUp({ value, format, duration = 1100 }: Props) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    const span = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : duration;
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = span === 0 ? 1 : Math.min(1, (now - start) / span);
      setShown(value * (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return (
    <>
      <span aria-hidden className="num">{format(shown)}</span>
      <span className="sr-only">{format(value)}</span>
    </>
  );
}
