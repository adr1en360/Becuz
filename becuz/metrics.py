"""The profit tree: profit = net_sales - cogs - wastage - opex. Cash gaps are measured separately.

Zetaris computes the daily figures in the becuz USL (daily_pnl). This module only
sums a period and compares it with the baseline. All arithmetic happens in SQL or
here, never in the model.

A period is any 1 to 28 days. Its baseline is the same days in the 4 periods before it, each moved back
by whole weeks, so every baseline window has the same weekdays as the period: a Friday-to-Sunday period
is compared with the 4 Friday-to-Sundays before it, and a 7-day period with the 4 weeks before it.
"""
from __future__ import annotations

from datetime import date, timedelta
from math import ceil

from becuz.adapters import Warehouse

COMPONENTS = ("net_sales_ngn", "cogs_ngn", "wastage_ngn", "opex_ngn", "profit_ngn")
BASELINE_PERIODS = 4
MAX_DAYS = 28

# Average per window over a set of days, and how many of those days have data. {usl} is the USL prefix.
PERIOD_TOTALS = "SELECT " + ", ".join(
    f"ROUND(SUM({c}) / {{windows}}, 2) AS {c}" for c in COMPONENTS
) + ", COUNT(*) AS days FROM {usl}.daily_pnl WHERE day IN ({days})"


class NotEnoughHistory(ValueError):
    pass


def baseline_days(start: date, end: date) -> list[date]:
    """Check the period is 1 to 28 real dates, and return the days of its 4 weekday-matched baseline windows.

    Only real dates pass, so model output can't inject into SQL built from them.
    """
    if not (isinstance(start, date) and isinstance(end, date) and 1 <= (end - start).days + 1 <= MAX_DAYS):
        raise ValueError(f"the period must be 1 to {MAX_DAYS} days: {start!r} to {end!r}")
    days = (end - start).days + 1
    step = 7 * ceil(days / 7)  # whole weeks, and never overlapping the period
    return sorted(start - timedelta(days=step * k - d) for k in range(1, BASELINE_PERIODS + 1) for d in range(days))


def date_list(days: list[date]) -> str:
    return ", ".join(f"DATE '{d.isoformat()}'" for d in days)


def period_totals(wh: Warehouse, days: list[date], windows: int) -> dict:
    row = wh.query(PERIOD_TOTALS.format(usl=wh.usl, days=date_list(days), windows=int(windows)))[0]
    if int(row["days"] or 0) < len(days):  # a missing day would read as zero profit
        raise NotEnoughHistory(f"the records cover {row['days'] or 0} of the {len(days)} days needed "
                               f"from {days[0]} to {days[-1]}")
    return {c: float(row[c] or 0) for c in COMPONENTS}


def profit_tree(wh: Warehouse, start: date, end: date) -> dict:
    """Each component for the period, its baseline (the average of the 4 baseline windows) and the change."""
    base = baseline_days(start, end)  # validates the dates first
    current = period_totals(wh, [start + timedelta(days=d) for d in range((end - start).days + 1)], windows=1)
    baseline = period_totals(wh, base, windows=BASELINE_PERIODS)
    return {c: {"current": current[c], "baseline": baseline[c], "change": round(current[c] - baseline[c], 2)}
            for c in COMPONENTS}
