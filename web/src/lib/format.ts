// Display formatting only. Every naira figure arrives from the agent; nothing is computed here.
const naira = new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 });
const day = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long" });
const dayYear = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" });

export const formatNaira = (n: number) => naira.format(Math.abs(n));

export function formatSigned(n: number) {
  if (n === 0) return formatNaira(0);
  return `${n < 0 ? "−" : "+"}${formatNaira(n)}`;
}

export const formatPct = (n: number) => `${Math.abs(n).toFixed(1)}%`;

const toDate = (iso: string) => new Date(`${iso}T00:00:00`);

export function formatRange(start: string, end: string) {
  return `${day.format(toDate(start))} to ${dayYear.format(toDate(end))}`;
}
