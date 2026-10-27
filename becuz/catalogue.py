"""The cause catalogue: what can explain a profit change, and the SQL that measures each cause.

Each cause has two Spark SQL templates over the becuz USL:
- `effect_sql` returns one row, `effect_ngn`: the cause's effect on the period's profit
  (negative is a loss), measured against the average of its 4 baseline windows (see metrics). For a cash cause
  (component "cash") it is the money recorded at the till that the bank never received.
- `records_sql` returns the record IDs behind that number, so every claim has receipts.

The Investigator runs them and the Checker re-runs them; the model never computes the number.
Templates use {usl}, {start}, {end} and {base_days} (the baseline dates as a SQL list).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from becuz.adapters import Warehouse
from becuz.metrics import BASELINE_PERIODS, baseline_days, date_list

WEEK = "BETWEEN DATE '{start}' AND DATE '{end}'"
BASE = "IN ({base_days})"
RECORD_LIMIT = 50


@dataclass(frozen=True)
class CauseSpec:
    cause_id: str
    title: str
    component: str  # profit tree node, as in schemas.Component, or "cash" for a cash gap
    origin: str
    nature: str
    sources: tuple[str, ...]
    effect_sql: str
    records_sql: str
    falsified_if: str  # what the data would show if this cause were not real
    table: str  # main USL table the evidence reads
    action: str  # what the owner can do next


CATALOGUE = {spec.cause_id: spec for spec in (
    CauseSpec(
        "supplier_cost_rise", "A supplier raised the unit cost of a product", "cogs", "external", "actionable",
        ("books_files", "pos_files"),
        # Cost in force, as in daily_pnl: a product's invoice cost holds from its invoice date until its next
        # invoice. The effect is the period's units at the cost in force on their day, against the baseline's
        # average cost in force per unit sold. Only products whose cost went up count.
        effect_sql=f"""SELECT ROUND(-COALESCE(SUM(CASE WHEN x.period_cost > x.period_qty * x.base_cost
                                     THEN x.period_cost - x.period_qty * x.base_cost END), 0), 2) AS effect_ngn
FROM (SELECT q.product_id,
             SUM(CASE WHEN q.day {WEEK} THEN q.qty * c.unit_cost_ngn END) AS period_cost,
             SUM(CASE WHEN q.day {WEEK} THEN q.qty END) AS period_qty,
             ROUND(SUM(CASE WHEN q.day {BASE} THEN q.qty * c.unit_cost_ngn END)
                   / SUM(CASE WHEN q.day {BASE} THEN q.qty END), 2) AS base_cost
      FROM (SELECT CAST(s.sold_at AS DATE) AS day, l.product_id, SUM(l.qty) AS qty
            FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
            WHERE CAST(s.sold_at AS DATE) {WEEK} OR CAST(s.sold_at AS DATE) {BASE}
            GROUP BY CAST(s.sold_at AS DATE), l.product_id) q
      JOIN (SELECT p.product_id, p.invoice_date AS valid_from,
                   COALESCE(MIN(n.invoice_date), DATE '9999-12-31') AS valid_until, p.unit_cost_ngn
            FROM (SELECT product_id, invoice_date, AVG(unit_cost_ngn) AS unit_cost_ngn
                  FROM {{usl}}.supplier_invoices GROUP BY product_id, invoice_date) p
            LEFT JOIN (SELECT DISTINCT product_id, invoice_date FROM {{usl}}.supplier_invoices) n
              ON n.product_id = p.product_id AND n.invoice_date > p.invoice_date
            GROUP BY p.product_id, p.invoice_date, p.unit_cost_ngn) c
        ON c.product_id = q.product_id AND q.day >= c.valid_from AND q.day < c.valid_until
      GROUP BY q.product_id) x""",
        # The invoices whose cost was in force during the period and is above the baseline cost in force.
        records_sql=f"""SELECT i.invoice_id AS record_id
FROM (SELECT p.product_id, p.invoice_date AS valid_from,
             COALESCE(MIN(n.invoice_date), DATE '9999-12-31') AS valid_until
      FROM (SELECT DISTINCT product_id, invoice_date FROM {{usl}}.supplier_invoices) p
      LEFT JOIN (SELECT DISTINCT product_id, invoice_date FROM {{usl}}.supplier_invoices) n
        ON n.product_id = p.product_id AND n.invoice_date > p.invoice_date
      GROUP BY p.product_id, p.invoice_date) c
JOIN {{usl}}.supplier_invoices i ON i.product_id = c.product_id AND i.invoice_date = c.valid_from
JOIN (SELECT q.product_id, ROUND(SUM(q.qty * b.unit_cost_ngn) / SUM(q.qty), 2) AS base_cost
      FROM (SELECT CAST(s.sold_at AS DATE) AS day, l.product_id, SUM(l.qty) AS qty
            FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
            WHERE CAST(s.sold_at AS DATE) {BASE}
            GROUP BY CAST(s.sold_at AS DATE), l.product_id) q
      JOIN (SELECT p.product_id, p.invoice_date AS valid_from,
                   COALESCE(MIN(n.invoice_date), DATE '9999-12-31') AS valid_until, p.unit_cost_ngn
            FROM (SELECT product_id, invoice_date, AVG(unit_cost_ngn) AS unit_cost_ngn
                  FROM {{usl}}.supplier_invoices GROUP BY product_id, invoice_date) p
            LEFT JOIN (SELECT DISTINCT product_id, invoice_date FROM {{usl}}.supplier_invoices) n
              ON n.product_id = p.product_id AND n.invoice_date > p.invoice_date
            GROUP BY p.product_id, p.invoice_date, p.unit_cost_ngn) b
        ON b.product_id = q.product_id AND q.day >= b.valid_from AND q.day < b.valid_until
      GROUP BY q.product_id) base ON base.product_id = i.product_id
WHERE c.valid_from <= DATE '{{end}}' AND c.valid_until > DATE '{{start}}' AND i.unit_cost_ngn > base.base_cost
ORDER BY i.invoice_id LIMIT {RECORD_LIMIT}""",
        falsified_if="unit costs on the period's invoices match the baseline",
        table="supplier_invoices",
        action="Compare prices from other suppliers for the affected product and review its shelf price.",
    ),
    CauseSpec(
        "promo_overrun", "A discount kept running after the promo ended", "net_sales", "internal", "actionable",
        ("pos_files",),
        effect_sql=f"""SELECT ROUND(-COALESCE(SUM(l.discount_ngn), 0), 2) AS effect_ngn
FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
JOIN {{usl}}.promos p ON p.promo_id = l.promo_id
WHERE CAST(s.sold_at AS DATE) {WEEK} AND CAST(s.sold_at AS DATE) > p.end_date""",
        records_sql=f"""SELECT l.line_id AS record_id FROM {{usl}}.sale_lines l
JOIN {{usl}}.sales s ON s.sale_id = l.sale_id JOIN {{usl}}.promos p ON p.promo_id = l.promo_id
WHERE CAST(s.sold_at AS DATE) {WEEK} AND CAST(s.sold_at AS DATE) > p.end_date
ORDER BY l.line_id LIMIT {RECORD_LIMIT}""",
        falsified_if="no promo discount was given after the promo's end date",
        table="sale_lines",
        action="Switch off the expired promo at the till and check which staff applied it.",
    ),
    CauseSpec(
        "wastage_spike", "More stock expired or was damaged than usual", "wastage", "internal", "actionable",
        ("pos_files",),
        effect_sql=f"""SELECT ROUND(-(COALESCE(SUM(CASE WHEN CAST(moved_at AS DATE) {WEEK} THEN qty * unit_cost_ngn END), 0)
                  - COALESCE(SUM(CASE WHEN CAST(moved_at AS DATE) {BASE} THEN qty * unit_cost_ngn END), 0) / {BASELINE_PERIODS}), 2)
       AS effect_ngn
FROM {{usl}}.stock_movements WHERE type IN ('expired', 'damaged')""",
        records_sql=f"""SELECT movement_id AS record_id FROM {{usl}}.stock_movements
WHERE type IN ('expired', 'damaged') AND CAST(moved_at AS DATE) {WEEK}
ORDER BY movement_id LIMIT {RECORD_LIMIT}""",
        falsified_if="expired and damaged stock in the period is no higher than usual",
        table="stock_movements",
        action="Order perishables in smaller batches and check storage for the affected items.",
    ),
    CauseSpec(
        "transfer_leakage", "Transfers recorded at the till never reached the bank", "cash", "internal", "actionable",
        ("pos_files", "bank_files"),
        effect_sql=f"""SELECT ROUND(-COALESCE(SUM(net_ngn), 0), 2) AS effect_ngn FROM {{usl}}.transfer_check
WHERE bank_txn_id IS NULL AND CAST(sold_at AS DATE) {WEEK}""",
        records_sql=f"""SELECT sale_id AS record_id FROM {{usl}}.transfer_check
WHERE bank_txn_id IS NULL AND CAST(sold_at AS DATE) {WEEK}
ORDER BY sale_id LIMIT {RECORD_LIMIT}""",
        falsified_if="every transfer sale in the period has a matching bank credit",
        table="transfer_check",
        action="Check these transfers against the bank app with the staff who recorded them.",
    ),
    CauseSpec(
        "pos_charge_rise", "The POS terminal charged a higher fee", "opex", "external", "actionable",
        ("bank_files",),
        # Extra charge in the period at the new rate, compared with the baseline rate.
        effect_sql=f"""SELECT ROUND(-(SUM(CASE WHEN CAST(posted_at AS DATE) {WEEK} AND channel = 'charge' THEN amount_ngn END)
       - SUM(CASE WHEN CAST(posted_at AS DATE) {WEEK} AND channel = 'pos_settlement' THEN amount_ngn END)
         * SUM(CASE WHEN CAST(posted_at AS DATE) {BASE} AND channel = 'charge' THEN amount_ngn END)
         / SUM(CASE WHEN CAST(posted_at AS DATE) {BASE} AND channel = 'pos_settlement' THEN amount_ngn END)), 2)
       AS effect_ngn
FROM {{usl}}.bank_statement""",
        records_sql=f"""SELECT txn_id AS record_id FROM {{usl}}.bank_statement
WHERE channel = 'charge' AND CAST(posted_at AS DATE) {WEEK}
ORDER BY txn_id LIMIT {RECORD_LIMIT}""",
        falsified_if="the charge rate in the period matches the baseline rate",
        table="bank_statement",
        action="Ask the POS provider to explain the fee change.",
    ),
    CauseSpec(
        "sales_volume_drop", "Fewer items sold than usual", "net_sales", "external", "temporary",
        ("pos_files", "books_files"),
        # Units sold above or below usual, valued at the usual profit per unit, so it does not
        # overlap with price, discount or cost causes.
        effect_sql=f"""SELECT ROUND(SUM((COALESCE(f.qty, 0) - COALESCE(b.qty, 0) / {BASELINE_PERIODS}) * (p.list_price_ngn - c.base_cost)), 2)
       AS effect_ngn
FROM {{usl}}.products p
JOIN (SELECT product_id, AVG(unit_cost_ngn) AS base_cost FROM {{usl}}.supplier_invoices
      WHERE invoice_date < DATE '{{start}}' GROUP BY product_id) c ON c.product_id = p.product_id
LEFT JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
           WHERE CAST(s.sold_at AS DATE) {WEEK} GROUP BY l.product_id) f ON f.product_id = p.product_id
LEFT JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
           WHERE CAST(s.sold_at AS DATE) {BASE} GROUP BY l.product_id) b ON b.product_id = p.product_id""",
        records_sql=f"""SELECT p.product_id AS record_id FROM {{usl}}.products p
LEFT JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
           WHERE CAST(s.sold_at AS DATE) {WEEK} GROUP BY l.product_id) f ON f.product_id = p.product_id
LEFT JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
           WHERE CAST(s.sold_at AS DATE) {BASE} GROUP BY l.product_id) b ON b.product_id = p.product_id
WHERE COALESCE(f.qty, 0) < COALESCE(b.qty, 0) / {BASELINE_PERIODS}
ORDER BY p.product_id LIMIT {RECORD_LIMIT}""",
        falsified_if="units sold in the period are at or above usual",
        table="sale_lines",
        action="Check stock levels and opening hours for the products that sold less.",
    ),
)}


@dataclass(frozen=True)
class Measurement:
    cause_id: str
    effect_ngn: float | None  # None when the data can't measure the cause: not tested, not zero
    row_ids: list[str]
    effect_sql: str
    records_sql: str


def render(template: str, usl: str, start: date, end: date) -> str:
    base = date_list(baseline_days(start, end))  # validates the dates first
    return template.format(usl=usl, start=start.isoformat(), end=end.isoformat(), base_days=base)


def measure(wh: Warehouse, cause_id: str, start: date, end: date) -> Measurement:
    spec = CATALOGUE[cause_id]  # unknown causes fail with KeyError: the model can only pick from the catalogue
    effect_sql = render(spec.effect_sql, wh.usl, start, end)
    records_sql = render(spec.records_sql, wh.usl, start, end)
    effect = wh.query(effect_sql)[0]["effect_ngn"]
    rows = [str(r["record_id"]) for r in wh.query(records_sql)]
    # + 0.0 turns -0.0 into 0.0 so a zero effect never prints as "-0".
    return Measurement(cause_id, None if effect is None else float(effect) + 0.0, rows, effect_sql, records_sql)
