"""Build the Becuz USL (Unified Semantic Layer) over the registered shop sources.

The USL declares the shop's tables and keys once; Zetaris turns every key into a
data-quality rule. Two derived tables do work inside Zetaris: transfer_check
(each transfer sale with its matching bank credit, if any) and daily_pnl (the
profit tree per day). The agent reads only these USL tables.

    uv run python -m scripts.zetaris_usl            # dry run: print statements
    uv run python -m scripts.zetaris_usl --apply    # run them, one statement per call
"""
from __future__ import annotations

import argparse

from scripts.admin import admin_env, run_plan

NAMESPACE = "lightning.metastore.becuz"
USL = f"{NAMESPACE}.becuz"

# Spark types; PKs are NOT NULL, FKs are declared inline (Zetaris generates a DQ rule for each key).
DDL = """
CREATE TABLE products (
    product_id varchar(8) NOT NULL PRIMARY KEY,
    sku varchar(16),
    name varchar(100),
    category varchar(32),
    unit varchar(16),
    list_price_ngn double,
    is_perishable boolean
);
CREATE TABLE staff (
    staff_id varchar(8) NOT NULL PRIMARY KEY,
    name varchar(64),
    role varchar(32)
);
CREATE TABLE sales (
    sale_id varchar(16) NOT NULL PRIMARY KEY,
    sold_at timestamp,
    staff_id varchar(8) FOREIGN KEY REFERENCES staff(staff_id),
    payment_method varchar(16),
    transfer_ref varchar(16),
    gross_ngn double,
    discount_ngn double,
    net_ngn double
);
CREATE TABLE sale_lines (
    line_id varchar(16) NOT NULL PRIMARY KEY,
    sale_id varchar(16) FOREIGN KEY REFERENCES sales(sale_id),
    product_id varchar(8) FOREIGN KEY REFERENCES products(product_id),
    qty int,
    unit_price_ngn double,
    discount_ngn double,
    promo_id varchar(8)
);
CREATE TABLE promos (
    promo_id varchar(8) NOT NULL PRIMARY KEY,
    product_id varchar(8) FOREIGN KEY REFERENCES products(product_id),
    pct_off int,
    start_date date,
    end_date date
);
CREATE TABLE stock_movements (
    movement_id varchar(16) NOT NULL PRIMARY KEY,
    product_id varchar(8) FOREIGN KEY REFERENCES products(product_id),
    moved_at timestamp,
    qty int,
    type varchar(16),
    unit_cost_ngn double,
    note varchar(64)
);
CREATE TABLE bank_statement (
    txn_id varchar(16) NOT NULL PRIMARY KEY,
    posted_at timestamp,
    direction varchar(8),
    amount_ngn double,
    channel varchar(16),
    ref varchar(32),
    counterparty varchar(64),
    narration varchar(128)
);
CREATE TABLE supplier_invoices (
    invoice_id varchar(16) NOT NULL PRIMARY KEY,
    invoice_date date,
    supplier_id varchar(8),
    supplier_name varchar(64),
    product_id varchar(8) FOREIGN KEY REFERENCES products(product_id),
    qty int,
    unit_cost_ngn double,
    total_ngn double
);
CREATE TABLE expenses (
    expense_id varchar(16) NOT NULL PRIMARY KEY,
    expense_date date,
    category varchar(16),
    amount_ngn double,
    note varchar(64)
);
CREATE TABLE fx_rates (
    rate_date date NOT NULL PRIMARY KEY,
    usd_ngn double
);
CREATE TABLE transfer_check (
    sale_id varchar(16) NOT NULL PRIMARY KEY,
    sold_at timestamp,
    staff_id varchar(8),
    net_ngn double,
    transfer_ref varchar(16),
    bank_txn_id varchar(16)
);
CREATE TABLE daily_pnl (
    day date NOT NULL PRIMARY KEY,
    net_sales_ngn double,
    cogs_ngn double,
    wastage_ngn double,
    opex_ngn double,
    leakage_ngn double,
    profit_ngn double
);
"""

# Base tables copy their source; NOT NULL key columns are wrapped in COALESCE as Zetaris requires.
COPIES = {
    "products": ("pos_files.products", "COALESCE(product_id, '') AS product_id, sku, name, category, unit, list_price_ngn, is_perishable"),
    "staff": ("pos_files.staff", "COALESCE(staff_id, '') AS staff_id, name, role"),
    "sales": ("pos_files.sales", "COALESCE(sale_id, '') AS sale_id, sold_at, staff_id, payment_method, transfer_ref, gross_ngn, discount_ngn, net_ngn"),
    "sale_lines": ("pos_files.sale_lines", "COALESCE(line_id, '') AS line_id, sale_id, product_id, qty, unit_price_ngn, discount_ngn, promo_id"),
    "promos": ("pos_files.promos", "COALESCE(promo_id, '') AS promo_id, product_id, pct_off, start_date, end_date"),
    "stock_movements": ("pos_files.stock_movements", "COALESCE(movement_id, '') AS movement_id, product_id, moved_at, qty, type, unit_cost_ngn, note"),
    "bank_statement": ("bank_files.bank_statement", "COALESCE(txn_id, '') AS txn_id, posted_at, direction, amount_ngn, channel, ref, counterparty, narration"),
    "supplier_invoices": ("books_files.supplier_invoices", "COALESCE(invoice_id, '') AS invoice_id, invoice_date, supplier_id, supplier_name, product_id, qty, unit_cost_ngn, total_ngn"),
    "expenses": ("books_files.expenses", "COALESCE(expense_id, '') AS expense_id, expense_date, category, amount_ngn, note"),
    "fx_rates": ("context_files.fx_rates", "COALESCE(`date`, DATE '1970-01-01') AS rate_date, usd_ngn"),
}

UNMATCHED_TRANSFERS = """pos_files.sales s
LEFT JOIN bank_files.bank_statement b ON b.ref = s.transfer_ref AND b.channel = 'transfer'
WHERE s.payment_method = 'transfer'"""

TRANSFER_CHECK = f"""SELECT COALESCE(s.sale_id, '') AS sale_id, s.sold_at, s.staff_id, s.net_ngn, s.transfer_ref, b.txn_id AS bank_txn_id
FROM {UNMATCHED_TRANSFERS}"""

# Profit tree per day: profit = net_sales - cogs - wastage - opex - leakage.
# COGS uses the unit cost on that week's supplier invoice (invoices land every Monday).
DAILY_PNL = f"""SELECT COALESCE(d.day, DATE '1970-01-01') AS day,
  ROUND(COALESCE(sa.v, 0), 2) AS net_sales_ngn,
  ROUND(COALESCE(co.v, 0), 2) AS cogs_ngn,
  ROUND(COALESCE(wa.v, 0), 2) AS wastage_ngn,
  ROUND(COALESCE(op.v, 0), 2) AS opex_ngn,
  ROUND(COALESCE(le.v, 0), 2) AS leakage_ngn,
  ROUND(COALESCE(sa.v, 0) - COALESCE(co.v, 0) - COALESCE(wa.v, 0) - COALESCE(op.v, 0) - COALESCE(le.v, 0), 2) AS profit_ngn
FROM (SELECT `date` AS day FROM context_files.fx_rates) d
LEFT JOIN (SELECT CAST(sold_at AS DATE) AS day, SUM(net_ngn) AS v FROM pos_files.sales GROUP BY CAST(sold_at AS DATE)) sa ON sa.day = d.day
LEFT JOIN (SELECT CAST(s.sold_at AS DATE) AS day, SUM(l.qty * i.unit_cost_ngn) AS v
           FROM pos_files.sale_lines l
           JOIN pos_files.sales s ON s.sale_id = l.sale_id
           JOIN books_files.supplier_invoices i ON i.product_id = l.product_id AND i.invoice_date = CAST(date_trunc('WEEK', s.sold_at) AS DATE)
           GROUP BY CAST(s.sold_at AS DATE)) co ON co.day = d.day
LEFT JOIN (SELECT CAST(moved_at AS DATE) AS day, SUM(qty * unit_cost_ngn) AS v FROM pos_files.stock_movements
           WHERE type IN ('expired', 'damaged') GROUP BY CAST(moved_at AS DATE)) wa ON wa.day = d.day
LEFT JOIN (SELECT expense_date AS day, SUM(amount_ngn) AS v FROM books_files.expenses GROUP BY expense_date) op ON op.day = d.day
LEFT JOIN (SELECT CAST(s.sold_at AS DATE) AS day, SUM(s.net_ngn) AS v FROM {UNMATCHED_TRANSFERS} AND b.txn_id IS NULL
           GROUP BY CAST(s.sold_at AS DATE)) le ON le.day = d.day"""


def activations() -> dict[str, str]:
    sql = {table: f"SELECT {cols} FROM {source}" for table, (source, cols) in COPIES.items()}
    sql["transfer_check"] = TRANSFER_CHECK
    sql["daily_pnl"] = DAILY_PNL
    return sql


def statements() -> list[str]:
    plan = [
        "CREATE NAMESPACE IF NOT EXISTS lightning.metastore",
        f"CREATE NAMESPACE IF NOT EXISTS {NAMESPACE}",
        # One call: a multi-table COMPILE must not be split at semicolons.
        f"COMPILE USL IF NOT EXISTS becuz DEPLOY NAMESPACE {NAMESPACE} DDL{DDL}",
    ]
    plan += [f"ACTIVATE USL TABLE {USL}.{table} AS\n{sql}" for table, sql in activations().items()]
    plan.append(f"REGISTER DQ transfer_reached_bank TABLE {USL}.transfer_check AS bank_txn_id IS NOT NULL")
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="run the statements against Zetaris")
    parser.add_argument("--start", type=int, default=1, help="resume at this statement number")
    args = parser.parse_args()
    loaded = admin_env()
    if loaded is None:
        return 1
    admin, env = loaded
    return run_plan(admin, statements(), args.apply, args.start, (env["ZETARIS_ADMIN_API_KEY"],))


if __name__ == "__main__":
    raise SystemExit(main())
