"use client";

import { useEffect, useRef, type CSSProperties, type ReactNode } from "react";

type Props = { children: ReactNode; delay?: number; as?: "div" | "li"; className?: string };

// Fades and rises once when scrolled into view. Content is visible by default; only elements below the fold
// are hidden, and never when the visitor prefers reduced motion. The attribute is set on the node directly so
// no render is needed.
export function Reveal({ children, delay = 0, as: Tag = "div", className }: Props) {
  const ref = useRef<HTMLDivElement & HTMLLIElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (el.getBoundingClientRect().top < window.innerHeight * 0.9) return;
    el.dataset.reveal = "hidden";
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.dataset.reveal = "shown";
          observer.disconnect();
        }
      },
      { threshold: 0.15 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag ref={ref} className={className} style={{ "--d": `${delay}ms` } as CSSProperties}>
      {children}
    </Tag>
  );
}
