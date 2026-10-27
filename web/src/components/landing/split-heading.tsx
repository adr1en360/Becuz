"use client";

import { useEffect, useRef, type CSSProperties } from "react";

type Props = { id: string; className?: string; children: string; as?: "h2" | "h3" };

// A heading whose words rise out of a mask when it scrolls into view. Headings already on screen at load are left
// alone, and the text is real text in the DOM, so readers and search see the whole heading at once.
export function SplitHeading({ id, className, children, as: Tag = "h2" }: Props) {
  const ref = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || el.getBoundingClientRect().top < window.innerHeight * 0.9) return;
    el.dataset.split = "hidden";
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.dataset.split = "shown";
          observer.disconnect();
        }
      },
      { threshold: 0.4 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag ref={ref} id={id} className={className}>
      {children.split(" ").map((word, i) => (
        <span key={i}>
          <span className="mask">
            <span className="split-word" style={{ "--d": `${i * 45}ms` } as CSSProperties}>
              {word}
            </span>
          </span>{" "}
        </span>
      ))}
    </Tag>
  );
}
