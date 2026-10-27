const motion =
  "inline-flex items-center justify-center gap-2 rounded-full font-bold transition-[background-color,color,transform] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)] hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.97] motion-reduce:transition-none motion-reduce:hover:translate-y-0 motion-reduce:active:scale-100";

const base = `${motion} h-12 px-6 text-base`;

export const primaryButton = `${base} bg-flare text-desk hover:bg-paper`;
export const smallPrimaryButton = `${motion} h-10 px-4 text-sm bg-flare text-desk hover:bg-paper sm:px-5 sm:text-base`;
export const secondaryButton = `${base} border-2 border-desk-line text-paper hover:border-paper hover:bg-paper hover:text-desk`;
