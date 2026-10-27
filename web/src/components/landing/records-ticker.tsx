import { demo } from "@/lib/demo-report";

const source: Record<string, string> = {
  "becuz.supplier_invoices": "supplier invoice",
  "becuz.stock_movements": "stock record",
  "becuz.sale_lines": "till sale",
  "becuz.sales": "till sale",
  "becuz.transfer_check": "transfer not in bank",
  "becuz.bank_statement": "bank line",
  "becuz.expenses": "expense",
  "becuz.expense_book": "expense",
};

const records = [...demo.causes, ...(demo.cash_gaps ?? [])].flatMap((c) =>
  c.evidence.flatMap((e) => e.row_ids.map((id) => ({ id, what: source[e.table] ?? e.table.replace("becuz.", "") }))),
);

// The record IDs behind the example run, sliding past: what "the records behind every cause" means.
export function RecordsTicker() {
  const half = (key: string) => (
    <ul className="flex shrink-0 items-center gap-8 pr-8" aria-hidden={key === "b"}>
      {records.map((r) => (
        <li key={`${key}-${r.id}`} className="flex items-center gap-2 whitespace-nowrap font-mono text-sm">
          <span className="size-1.5 rounded-full bg-flare" aria-hidden />
          <span className="text-paper">{r.id}</span>
          <span className="text-desk-muted">{r.what}</span>
        </li>
      ))}
    </ul>
  );
  return (
    <section aria-label={`${records.length} records behind the example answer`} className="border-y border-desk-line py-5">
      <div className="marquee-mask overflow-hidden">
        <div className="marquee flex w-max">
          {half("a")}
          {half("b")}
        </div>
      </div>
    </section>
  );
}

export const recordCount = records.length;
