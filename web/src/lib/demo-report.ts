import type { Investigation } from "@/lib/investigation";
import saved from "@/data/example-s01.json";

// The landing page shows a real saved run (output_examples/example_1_output.json, copied here and kept equal by a
// Python test), so no figure on it is typed by hand.
export const demo = saved as unknown as Investigation;
export const demoDays = demo.frame.days ?? 7;
