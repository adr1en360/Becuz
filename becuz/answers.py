"""Direct answers to everyday questions about the shop's money, each one read-only SQL with its records.

The investigation explains why profit moved. These answer what happened: what sold most or least, how much
the shop sold, made and spent, what it spent money on, and whether any money is missing. Each compares the
period with the same baseline windows as the investigation (metrics.baseline_days); SQL computes every figure.
"""
from __future__ import annotations

from datetime import date, timedelta

from becuz.adapters import Warehouse
from becuz.metrics import BASELINE_PERIODS, PERIOD_TOTALS, baseline_days, date_list
from becuz.words import naira, plural, span

ROWS = 5
NOW = "BETWEEN DATE '{start}' AND DATE '{end}'"
BASE = "IN ({base_days})"

SELLERS = f"""SELECT p.name AS label,
       ROUND(SUM(CASE WHEN CAST(s.sold_at AS DATE) {NOW} THEN l.qty * l.unit_price_ngn - l.discount_ngn ELSE 0 END), 2) AS value_ngn,
       ROUND(SUM(CASE WHEN CAST(s.sold_at AS DATE) {BASE} THEN l.qty * l.unit_price_ngn - l.discount_ngn ELSE 0 END) / {BASELINE_PERIODS}, 2) AS usual_ngn,
       SUM(CASE WHEN CAST(s.sold_at AS DATE) {NOW} THEN l.qty ELSE 0 END) AS units,
       MIN(p.product_id) AS record_id
FROM {{usl}}.sale_lines l JOIN {{usl}}.sales s ON s.sale_id = l.sale_id JOIN {{usl}}.products p ON p.product_id = l.product_id
WHERE CAST(s.sold_at AS DATE) {NOW} OR CAST(s.sold_at AS DATE) {BASE}
GROUP BY p.name ORDER BY value_ngn {{order}}, p.name LIMIT {ROWS}"""

EXPENSES = f"""SELECT category AS label,
       ROUND(SUM(CASE WHEN expense_date {NOW} THEN amount_ngn ELSE 0 END), 2) AS value_ngn,
       ROUND(SUM(CASE WHEN expense_date {BASE} THEN amount_ngn ELSE 0 END) / {BASELINE_PERIODS}, 2) AS usual_ngn,
       SUM(CASE WHEN expense_date {NOW} THEN 1 ELSE 0 END) AS units,
       MIN(CASE WHEN expense_date {NOW} THEN expense_id END) AS record_id
FROM {{usl}}.expenses WHERE expense_date {NOW} OR expense_date {BASE}
GROUP BY category ORDER BY value_ngn DESC, category LIMIT {ROWS}"""

MISSING = f"""SELECT sale_id AS label, net_ngn AS value_ngn, sale_id AS record_id FROM {{usl}}.transfer_check
WHERE bank_txn_id IS NULL AND CAST(sold_at AS DATE) {NOW} ORDER BY net_ngn DESC, sale_id"""

LABELS = {"net_sales_ngn": "Sales", "cogs_ngn": "Cost of stock sold", "wastage_ngn": "Wasted stock",
          "opex_ngn": "Running costs", "profit_ngn": "Profit"}


def render(template: str, usl: str, start: date, end: date, **extra) -> str:
    base = date_list(baseline_days(start, end))  # validates the dates first
    return template.format(usl=usl, start=start.isoformat(), end=end.isoformat(), base_days=base, **extra)


def compare(now: float, usual: float | None) -> str:
    if not usual:
        return ""
    pct = round((now - usual) / abs(usual) * 100)
    return f", {abs(pct)}% {'above' if pct > 0 else 'below'} usual" if pct else ", the same as usual"


def answer(kind: str, wh: Warehouse, start: date, end: date, tree: dict, question: str = "") -> dict:
    """One direct answer: a sentence, up to 5 rows, the SQL and the records behind it."""
    noun, when = span(start, end)
    if kind == "totals":
        sql = PERIOD_TOTALS.format(usl=wh.usl, days=date_list([start + timedelta(days=d) for d in range((end - start).days + 1)]), windows=1)
        rows = [{"label": LABELS[c], "value_ngn": tree[c]["current"], "usual_ngn": tree[c]["baseline"], "detail": ""}
                for c in LABELS]
        sentence = (f"{when[:1].upper() + when[1:]} you sold {naira(tree['net_sales_ngn']['current'])} and made "
                    f"{naira(tree['profit_ngn']['current'])} profit{compare(tree['profit_ngn']['current'], tree['profit_ngn']['baseline'])}.")
        return {"kind": kind, "sentence": sentence, "rows": rows, "sql": sql, "row_ids": []}
    if kind == "missing_money":
        sql = render(MISSING, wh.usl, start, end)
        found = wh.query(sql)
        total = sum(float(r["value_ngn"]) for r in found)
        rows = [{"label": str(r["label"]), "value_ngn": float(r["value_ngn"]), "usual_ngn": None,
                 "detail": "transfer sale with no bank credit"} for r in found[:ROWS]]
        sentence = (f"{naira(total)} from {plural(len(found), 'transfer sale')} {when} never reached the bank."
                    if found else f"Every transfer sale {when} reached the bank.")
        return {"kind": kind, "sentence": sentence, "rows": rows, "sql": sql, "row_ids": [str(r["record_id"]) for r in found]}
    least = kind == "top_sellers" and any(w in question.lower() for w in ("least", "lowest", "worst", "slowest"))
    template = EXPENSES if kind == "expenses" else SELLERS
    sql = render(template, wh.usl, start, end, order="ASC" if least else "DESC")
    found = wh.query(sql)
    rows = [{"label": str(r["label"]), "value_ngn": float(r["value_ngn"] or 0), "usual_ngn": float(r["usual_ngn"] or 0),
             "detail": plural(int(r["units"] or 0), "unit" if kind == "top_sellers" else "payment")} for r in found]
    if not rows:
        return {"kind": kind, "sentence": f"No records {when} to answer that.", "rows": [], "sql": sql, "row_ids": []}
    top = rows[0]
    if kind == "expenses":
        sentence = f"Your biggest spend {when} was {top['label']}: {naira(top['value_ngn'])}{compare(top['value_ngn'], top['usual_ngn'])}."
    else:
        sentence = (f"{top['label']} sold {'least' if least else 'most'} {when}: {naira(top['value_ngn'])} from "
                    f"{top['detail']}{compare(top['value_ngn'], top['usual_ngn'])}.")
    return {"kind": kind, "sentence": sentence, "rows": rows, "sql": sql,
            "row_ids": [str(r["record_id"]) for r in found if r["record_id"]]}

