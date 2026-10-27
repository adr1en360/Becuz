"use client";

import { useEffect, useRef, useState } from "react";

// True once the element has scrolled into view. Drives one-shot reveals (stamps, bars, count-ups).
// It starts false on the server and in the browser alike, so the first paint matches and the reveal really plays.
export function useSeen<T extends HTMLElement>(threshold = 0.3) {
  const ref = useRef<T>(null);
  const [seen, setSeen] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setSeen(true);
          observer.disconnect();
        }
      },
      { threshold },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return [ref, seen] as const;
}
