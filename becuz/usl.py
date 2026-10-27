"""The Becuz data contract: the four Zetaris sources and the becuz USL built over them.

One definition serves both engines: Zetaris activates these queries, and sample
mode runs the same Spark SQL on DuckDB (see adapters/local_sql.py).
"""
from __future__ import annotations

# Logical source -> tables, matching docs/PRD.md section 4.
SOURCES = {
    "pos_files": ["products", "staff", "sales", "sale_lines", "promos", "stock_movements"],
    "bank_files": ["bank_statement"],
    "books_files": ["supplier_invoices", "expense_book"],
    "context_files": ["fx_rates", "calendar"],
}
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
    # The expense book's cover columns feed daily_pnl straight from the source; the USL table keeps the plain book.
    "expenses": ("books_files.expense_book", "COALESCE(expense_id, '') AS expense_id, expense_date, category, amount_ngn, note"),
    "fx_rates": ("context_files.fx_rates", "COALESCE(`date`, DATE '1970-01-01') AS rate_date, usd_ngn"),}

# Cost in force: each product's invoice cost holds from its invoice date until the product's next
# invoice date (valid_until is exclusive; the last cost runs on). Same-day invoices are averaged.
# Plain joins and GROUP BY, no window functions. catalogue.supplier_cost_rise uses the same rule.
COST_PERIODS = """SELECT p.product_id, p.invoice_date AS valid_from,
  COALESCE(MIN(n.invoice_date), DATE '9999-12-31') AS valid_until, p.unit_cost_ngn
FROM (SELECT product_id, CAST(invoice_date AS DATE) AS invoice_date, AVG(unit_cost_ngn) AS unit_cost_ngn
      FROM books_files.supplier_invoices GROUP BY product_id, CAST(invoice_date AS DATE)) p
LEFT JOIN (SELECT DISTINCT product_id, CAST(invoice_date AS DATE) AS invoice_date FROM books_files.supplier_invoices) n
  ON n.product_id = p.product_id AND n.invoice_date > p.invoice_date
GROUP BY p.product_id, p.invoice_date, p.unit_cost_ngn"""

UNMATCHED_TRANSFERS = """pos_files.sales s
LEFT JOIN bank_files.bank_statement b ON b.ref = s.transfer_ref AND b.channel = 'transfer'
WHERE s.payment_method = 'transfer'"""

TRANSFER_CHECK = f"""SELECT COALESCE(s.sale_id, '') AS sale_id, s.sold_at, s.staff_id, s.net_ngn, s.transfer_ref, b.txn_id AS bank_txn_id
FROM {UNMATCHED_TRANSFERS}"""

# Profit tree per day: profit = net_sales - cogs - wastage - opex.
# leakage_ngn (transfer sales with no bank credit) is a cash gap, not a cost: the sale happened, so it
# stays in profit, and the agent reports the missing money separately.
# The spine is the calendar (every day from the first to the last data day).
# COGS prices each day's units at the cost in force that day: the latest invoice on or before it.
# Opex is spread evenly over an expense's cover period when it has one, else booked on its date.
DAILY_PNL = f"""SELECT COALESCE(d.day, DATE '1970-01-01') AS day,
  ROUND(COALESCE(sa.v, 0), 2) AS net_sales_ngn,
  ROUND(COALESCE(co.v, 0), 2) AS cogs_ngn,
  ROUND(COALESCE(wa.v, 0), 2) AS wastage_ngn,
  ROUND(COALESCE(op.v, 0), 2) AS opex_ngn,
  ROUND(COALESCE(le.v, 0), 2) AS leakage_ngn,
  ROUND(COALESCE(sa.v, 0) - COALESCE(co.v, 0) - COALESCE(wa.v, 0) - COALESCE(op.v, 0), 2) AS profit_ngn
FROM (SELECT CAST(cal_date AS DATE) AS day FROM context_files.calendar) d
LEFT JOIN (SELECT CAST(sold_at AS DATE) AS day, SUM(net_ngn) AS v FROM pos_files.sales GROUP BY CAST(sold_at AS DATE)) sa ON sa.day = d.day
LEFT JOIN (SELECT q.day, SUM(q.qty * c.unit_cost_ngn) AS v
           FROM (SELECT CAST(s.sold_at AS DATE) AS day, l.product_id, SUM(l.qty) AS qty
                 FROM pos_files.sale_lines l JOIN pos_files.sales s ON s.sale_id = l.sale_id
                 GROUP BY CAST(s.sold_at AS DATE), l.product_id) q
           JOIN ({COST_PERIODS}) c ON c.product_id = q.product_id AND q.day >= c.valid_from AND q.day < c.valid_until
           GROUP BY q.day) co ON co.day = d.day
LEFT JOIN (SELECT CAST(moved_at AS DATE) AS day, SUM(qty * unit_cost_ngn) AS v FROM pos_files.stock_movements
           WHERE type IN ('expired', 'damaged') GROUP BY CAST(moved_at AS DATE)) wa ON wa.day = d.day
LEFT JOIN (SELECT CAST(k.cal_date AS DATE) AS day,
                  SUM(e.amount_ngn / (DATEDIFF(e.span_end, e.span_start) + 1)) AS v
           FROM context_files.calendar k
           JOIN (SELECT amount_ngn, CAST(COALESCE(cover_start, expense_date) AS DATE) AS span_start,
                        CAST(COALESCE(cover_end, expense_date) AS DATE) AS span_end
                 FROM books_files.expense_book) e
             ON CAST(k.cal_date AS DATE) >= e.span_start AND CAST(k.cal_date AS DATE) <= e.span_end
           GROUP BY CAST(k.cal_date AS DATE)) op ON op.day = d.day
LEFT JOIN (SELECT CAST(s.sold_at AS DATE) AS day, SUM(s.net_ngn) AS v FROM {UNMATCHED_TRANSFERS} AND b.txn_id IS NULL
           GROUP BY CAST(s.sold_at AS DATE)) le ON le.day = d.day"""


def activations() -> dict[str, str]:
    sql = {table: f"SELECT {cols} FROM {source}" for table, (source, cols) in COPIES.items()}
    sql["transfer_check"] = TRANSFER_CHECK
    sql["daily_pnl"] = DAILY_PNL
    return sql
