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

export function tableChipName(table: string): string {
  const clean = table.replace(/^becuz\./, "").toLowerCase();
  switch (clean) {
    case "supplier_invoices":
      return "Supplier invoices";
    case "sales":
    case "sale_lines":
      return "Till sales";
    case "stock_movements":
      return "Stock records";
    case "bank_statement":
      return "Bank statement";
    case "transfer_check":
      return "Till transfers vs bank";
    case "promos":
      return "Promotions";
    case "expenses":
    case "expense_book":
      return "Expense book";
    case "daily_pnl":
      return "Daily profit and loss";
    case "products":
      return "Product list";
    default:
      return clean.replace(/_/g, " ");
  }
}

