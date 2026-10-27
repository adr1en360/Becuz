// The hero and closing background: a ledger dot grid with naira flowing along a few lines through it.
// Decorative only; it holds still when the visitor prefers reduced motion.
const paths = [
  "M-40 620 C 220 560, 380 700, 620 560 S 1000 380, 1260 420",
  "M-40 300 C 180 360, 360 220, 600 300 S 980 520, 1260 460",
  "M200 860 C 320 640, 560 640, 700 480 S 900 120, 1100 -40",
];

export function Backdrop({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}>
      <div className="ledger-grid absolute inset-0" />
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice">
        {paths.map((d, i) => (
          <g key={d}>
            <path d={d} className="flow-path" style={{ animationDelay: `${-i * 0.9}s` }} />
            <path d={d} pathLength={1000} className="flow-pulse" style={{ animationDelay: `${i * 1.7}s` }} />
          </g>
        ))}
      </svg>
    </div>
  );
}
