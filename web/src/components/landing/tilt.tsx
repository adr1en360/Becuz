"use client";

import { useEffect, useRef, type ReactNode } from "react";

const STIFFNESS = 170;
const DAMPING = 22;

// Leans toward the pointer on a spring, so it carries momentum and settles instead of snapping.
// Mouse only, and off when the visitor prefers reduced motion.
export function Tilt({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const s = useRef({ x: 0, y: 0, vx: 0, vy: 0, tx: 0, ty: 0, raf: 0, last: 0 });

  useEffect(() => {
    const state = s.current;
    return () => cancelAnimationFrame(state.raf);
  }, []);

  function step(now: number) {
    const el = ref.current;
    const state = s.current;
    if (!el) return;
    const dt = Math.min(0.032, (now - state.last) / 1000 || 0.016);
    state.last = now;
    state.vx += ((state.tx - state.x) * STIFFNESS - state.vx * DAMPING) * dt;
    state.vy += ((state.ty - state.y) * STIFFNESS - state.vy * DAMPING) * dt;
    state.x += state.vx * dt;
    state.y += state.vy * dt;
    el.style.transform = `perspective(1000px) rotateX(${state.y.toFixed(2)}deg) rotateY(${state.x.toFixed(2)}deg)`;
    const settled = Math.abs(state.vx) + Math.abs(state.vy) + Math.abs(state.tx - state.x) + Math.abs(state.ty - state.y) < 0.02;
    if (settled) {
      el.style.transform = "";
      state.raf = 0;
    } else {
      state.raf = requestAnimationFrame(step);
    }
  }

  function aim(x: number, y: number) {
    const state = s.current;
    state.tx = x;
    state.ty = y;
    if (!state.raf) {
      state.last = performance.now();
      state.raf = requestAnimationFrame(step);
    }
  }

  function move(e: React.PointerEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el || e.pointerType !== "mouse" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const box = el.getBoundingClientRect();
    aim(((e.clientX - box.left) / box.width - 0.5) * 8, -((e.clientY - box.top) / box.height - 0.5) * 6);
  }

  return (
    <div ref={ref} onPointerMove={move} onPointerLeave={() => aim(0, 0)} className={`will-change-transform ${className ?? ""}`}>
      {children}
    </div>
  );
}
