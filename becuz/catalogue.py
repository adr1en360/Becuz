"""The cause catalogue: what can explain a profit change, and the SQL that measures each cause.

Each cause has two Spark SQL templates over the becuz USL:
- `effect_sql` returns one row, `effect_ngn`: the cause's effect on this week's profit
  (negative is a loss), measured against the average of the 4 weeks before.
- `records_sql` returns the record IDs behind that number, so every claim has receipts.

The Investigator runs them and the Checker re-runs them; the model never computes the number.
Templates use {usl}, {start}, {end}, {base_start} and {base_end}.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from becuz.adapters import Warehouse
from becuz.metrics import BASELINE_WEEKS, week

WEEK = "BETWEEN DATE '{start}' AND DATE '{end}'"
BASE = "BETWEEN DATE '{base_start}' AND DATE '{base_end}'"
RECORD_LIMIT = 50


@dataclass(frozen=True)
class CauseSpec:
    cause_id: str
    title: str
    component: str  # profit tree node, as in schemas.Component
    origin: str
    nature: str
    sources: tuple[str, ...]
    effect_sql: str
    records_sql: str
    falsified_if: str  # what the data would show if this cause were not real


CATALOGUE = {spec.cause_id: spec for spec in (
    CauseSpec(
        "supplier_cost_rise", "A supplier raised the unit cost of a product", "cogs", "external", "actionable",
        ("books_files", "pos_files"),
        effect_sql=f"""SELECT ROUND(-COALESCE(SUM(q.qty * (c.final_cost - c.base_cost)), 0), 2) AS effect_ngn
FROM (SELECT product_id,
             AVG(CASE WHEN invoice_date {WEEK} THEN unit_cost_ngn END) AS final_cost,
             AVG(CASE WHEN invoice_date {BASE} THEN unit_cost_ngn END) AS base_cost
      FROM {{usl}}.supplier_invoices GROUP BY product_id) c
JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l
      JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
      WHERE CAST(s.sold_at AS DATE) {WEEK} GROUP BY l.product_id) q ON q.product_id = c.product_id
WHERE c.final_cost > c.base_cost""",
        records_sql=f"""SELECT i.invoice_id AS record_id FROM {{usl}}.supplier_invoices i
JOIN (SELECT product_id, AVG(unit_cost_ngn) AS base_cost FROM {{usl}}.supplier_invoices
      WHERE invoice_date {BASE} GROUP BY product_id) b ON b.product_id = i.product_id
WHERE i.invoice_date {WEEK} AND i.unit_cost_ngn > b.base_cost
ORDER BY i.invoice_id LIMIT {RECORD_LIMIT}""",
        falsified_if="unit costs on this week's invoices match the baseline weeks",
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
    ),
    CauseSpec(
        "wastage_spike", "More stock expired or was damaged than usual", "wastage", "internal", "actionable",
        ("pos_files",),
        effect_sql=f"""SELECT ROUND(-(COALESCE(SUM(CASE WHEN CAST(moved_at AS DATE) {WEEK} THEN qty * unit_cost_ngn END), 0)
                  - COALESCE(SUM(CASE WHEN CAST(moved_at AS DATE) {BASE} THEN qty * unit_cost_ngn END), 0) / {BASELINE_WEEKS}), 2)
       AS effect_ngn
FROM {{usl}}.stock_movements WHERE type IN ('expired', 'damaged')""",
        records_sql=f"""SELECT movement_id AS record_id FROM {{usl}}.stock_movements
WHERE type IN ('expired', 'damaged') AND CAST(moved_at AS DATE) {WEEK}
ORDER BY movement_id LIMIT {RECORD_LIMIT}""",
        falsified_if="this week's expired and damaged stock is no higher than a usual week",
    ),
    CauseSpec(
        "transfer_leakage", "Transfers recorded at the till never reached the bank", "leakage", "internal", "actionable",
        ("pos_files", "bank_files"),
        effect_sql=f"""SELECT ROUND(-COALESCE(SUM(net_ngn), 0), 2) AS effect_ngn FROM {{usl}}.transfer_check
WHERE bank_txn_id IS NULL AND CAST(sold_at AS DATE) {WEEK}""",
        records_sql=f"""SELECT sale_id AS record_id FROM {{usl}}.transfer_check
WHERE bank_txn_id IS NULL AND CAST(sold_at AS DATE) {WEEK}
ORDER BY sale_id LIMIT {RECORD_LIMIT}""",
        falsified_if="every transfer sale this week has a matching bank credit",
    ),
    CauseSpec(
        "pos_charge_rise", "The POS terminal charged a higher fee", "opex", "external", "actionable",
        ("bank_files",),
        # Extra charge this week at the new rate, compared with the baseline rate.
        effect_sql=f"""SELECT ROUND(-(SUM(CASE WHEN CAST(posted_at AS DATE) {WEEK} AND channel = 'charge' THEN amount_ngn END)
       - SUM(CASE WHEN CAST(posted_at AS DATE) {WEEK} AND channel = 'pos_settlement' THEN amount_ngn END)
         * SUM(CASE WHEN CAST(posted_at AS DATE) {BASE} AND channel = 'charge' THEN amount_ngn END)
         / SUM(CASE WHEN CAST(posted_at AS DATE) {BASE} AND channel = 'pos_settlement' THEN amount_ngn END)), 2)
       AS effect_ngn
FROM {{usl}}.bank_statement""",
        records_sql=f"""SELECT txn_id AS record_id FROM {{usl}}.bank_statement
WHERE channel = 'charge' AND CAST(posted_at AS DATE) {WEEK}
ORDER BY txn_id LIMIT {RECORD_LIMIT}""",
        falsified_if="the charge rate this week matches the baseline rate",
    ),
    CauseSpec(
        "sales_volume_drop", "Fewer items sold than in a usual week", "net_sales", "external", "temporary",
        ("pos_files", "books_files"),
        # Units sold above or below a usual week, valued at the usual profit per unit, so it does not
        # overlap with price, discount or cost causes.
        effect_sql=f"""SELECT ROUND(SUM((COALESCE(f.qty, 0) - COALESCE(b.qty, 0) / {BASELINE_WEEKS}) * (p.list_price_ngn - c.base_cost)), 2)
       AS effect_ngn
FROM {{usl}}.products p
JOIN (SELECT product_id, AVG(unit_cost_ngn) AS base_cost FROM {{usl}}.supplier_invoices
      WHERE invoice_date {BASE} GROUP BY product_id) c ON c.product_id = p.product_id
LEFT JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
           WHERE CAST(s.sold_at AS DATE) {WEEK} GROUP BY l.product_id) f ON f.product_id = p.product_id
LEFT JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
           WHERE CAST(s.sold_at AS DATE) {BASE} GROUP BY l.product_id) b ON b.product_id = p.product_id""",
        records_sql=f"""SELECT p.product_id AS record_id FROM {{usl}}.products p
LEFT JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
           WHERE CAST(s.sold_at AS DATE) {WEEK} GROUP BY l.product_id) f ON f.product_id = p.product_id
LEFT JOIN (SELECT l.product_id, SUM(l.qty) AS qty FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id
           WHERE CAST(s.sold_at AS DATE) {BASE} GROUP BY l.product_id) b ON b.product_id = p.product_id
WHERE COALESCE(f.qty, 0) < COALESCE(b.qty, 0) / {BASELINE_WEEKS}
ORDER BY p.product_id LIMIT {RECORD_LIMIT}""",
        falsified_if="this week's units sold are at or above a usual week",
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
    base_start, base_end = week(start, end)
    return template.format(usl=usl, start=start.isoformat(), end=end.isoformat(),
                           base_start=base_start.isoformat(), base_end=base_end.isoformat())


def measure(wh: Warehouse, cause_id: str, start: date, end: date) -> Measurement:
    spec = CATALOGUE[cause_id]  # unknown causes fail with KeyError: the model can only pick from the catalogue
    effect_sql = render(spec.effect_sql, wh.usl, start, end)
    records_sql = render(spec.records_sql, wh.usl, start, end)
    effect = wh.query(effect_sql)[0]["effect_ngn"]
    rows = [str(r["record_id"]) for r in wh.query(records_sql)]
    return Measurement(cause_id, None if effect is None else float(effect), rows, effect_sql, records_sql)
