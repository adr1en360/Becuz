// Decorative bars drawn from the run id, so each receipt has its own code.
export function Barcode({ seed }: { seed: string }) {
  let h = 2166136261;
  const widths: number[] = [];
  for (let i = 0; widths.length < 46; i++) {
    h = Math.imul(h ^ seed.charCodeAt(i % seed.length), 16777619) >>> 0;
    widths.push(1 + (h % 4));
  }
  let x = 0;
  const bars = widths.map((w, i) => {
    const bar = i % 2 === 0 ? <rect key={i} x={x} y={0} width={w} height={44} fill="currentColor" /> : null;
    x += w;
    return bar;
  });
  return (
    <svg viewBox={`0 0 ${x} 44`} className="h-11 w-full max-w-64" preserveAspectRatio="none" aria-hidden>
      {bars}
    </svg>
  );
}
