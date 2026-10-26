const base =
  "inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-base font-bold transition-[background-color,color,transform] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)] hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.97] motion-reduce:transition-none motion-reduce:hover:translate-y-0 motion-reduce:active:scale-100";

export const primaryButton = `${base} bg-flare text-desk hover:bg-paper`;
export const secondaryButton = `${base} border-2 border-desk-line text-paper hover:border-paper hover:bg-paper hover:text-desk`;
