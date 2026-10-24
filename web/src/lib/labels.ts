import type { Investigation } from "./investigation";

type Cause = Investigation["causes"][number];
type Component = Cause["component"];
type Source = Cause["depends_on_sources"][number];
type TreeStatus = Investigation["tree"][number]["status"];

export const componentLabel: Record<Component, string> = {
  net_sales: "Sales",
  cogs: "Cost of stock sold",
  wastage: "Wasted stock",
  opex: "Running costs",
};

export const sourceLabel: Record<Source, string> = {
  pos_files: "till records",
  bank_files: "bank statement",
  books_files: "supplier invoices and expenses",
  context_files: "outside data",
};

export const treeStatusLabel: Record<TreeStatus, string> = {
  explained: "Explained",
  partly_explained: "Partly explained",
  unexplained: "Not explained",
  no_change: "No change",
};

export const originLabel: Record<Cause["origin"], string> = {
  internal: "Inside the shop",
  external: "Outside the shop",
};

export const natureLabel: Record<Cause["nature"], string> = {
  actionable: "You can act on it",
  temporary: "Likely to pass",
};
