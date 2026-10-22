"""The profit tree: profit = net_sales - cogs - wastage - opex - leakage.

Zetaris computes the daily figures in the becuz USL (daily_pnl). This module only
sums a period and compares it with the baseline. All arithmetic happens in SQL or
here, never in the model.
"""
from __future__ import annotations

from datetime import date, timedelta

from becuz.adapters import Warehouse

COMPONENTS = ("net_sales_ngn", "cogs_ngn", "wastage_ngn", "opex_ngn", "leakage_ngn", "profit_ngn")
BASELINE_WEEKS = 4

# Average per week over [start, end]. {usl} is the warehouse's USL prefix.
PERIOD_TOTALS = "SELECT " + ", ".join(
    f"ROUND(SUM({c}) / {{weeks}}, 2) AS {c}" for c in COMPONENTS
) + " FROM {usl}.daily_pnl WHERE day BETWEEN DATE '{start}' AND DATE '{end}'"


def period_totals(wh: Warehouse, start: date, end: date, weeks: int = 1) -> dict:
    # Only real dates reach the SQL text, so model output can't inject into it.
    if not (isinstance(start, date) and isinstance(end, date) and start <= end):
        raise ValueError(f"bad period: {start!r} to {end!r}")
    sql = PERIOD_TOTALS.format(usl=wh.usl, start=start.isoformat(), end=end.isoformat(), weeks=int(weeks))
    row = wh.query(sql)[0]
    return {c: float(row[c] or 0) for c in COMPONENTS}


def profit_tree(wh: Warehouse, start: date, end: date) -> dict:
    """For a one-week period: each component, its baseline (the 4 prior weeks' average) and the change."""
    current = period_totals(wh, start, end)
    base_start = start - timedelta(weeks=BASELINE_WEEKS)
    baseline = period_totals(wh, base_start, start - timedelta(days=1), weeks=BASELINE_WEEKS)
    return {c: {"current": current[c], "baseline": baseline[c], "change": round(current[c] - baseline[c], 2)}
            for c in COMPONENTS}
