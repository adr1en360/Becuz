import type { ReactNode } from "react";

export function Receipt({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`receipt paper print mx-auto w-full max-w-[40rem] px-6 py-10 sm:px-10 ${className}`}>{children}</div>;
}

export function Leader({ label, value, valueClass = "" }: { label: ReactNode; value: ReactNode; valueClass?: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="font-semibold">{label}</span>
      <span className="leader" aria-hidden />
      <span className={`num font-mono font-medium ${valueClass}`}>{value}</span>
    </div>
  );
}

export function SectionTitle({ id, children }: { id: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline gap-3">
      <h2 id={id} className="font-mono text-sm font-medium uppercase tracking-[0.16em]">
        {children}
      </h2>
      <span className="leader" aria-hidden />
    </div>
  );
}

export const Divider = () => <hr className="cut-line my-9 border-0" />;
