import { ReportOutline } from "./report-outline";

export function EmptyState() {
  return (
    <div className="flex flex-col gap-5">
      <p className="font-mono text-xs uppercase tracking-[0.16em] text-desk-muted">Your receipt prints here</p>
      <ReportOutline />
    </div>
  );
}
