"""Seeded synthetic shop generator: 20 weeks of records for one Nigerian mini-mart.

Writes one CSV per table plus answer_key.json into data/scenarios/<scenario>/.
All data is synthetic. Causes are planted only in the final week.

Costs follow real rhythms rather than one Monday lump: rent, salaries and the waste levy are paid
monthly with a cover period (cover_start to cover_end) that the USL spreads per day; diesel, transport
and electricity tokens are paid on varying days with no cover period; supplier deliveries land on
varying weekdays, and a sale is costed at the latest invoice on or before its day.

    uv run python -m data.generator s01
"""
from __future__ import annotations

import csv
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "scenarios"
START = date(2026, 4, 20)  # a Monday; 26 weeks to Sunday 18 Oct 2026, the last week is the one investigated
WEEKS = 26  # enough for a 28-day period plus its 4 baseline windows, with room to start it earlier
FINAL = WEEKS - 1
BASELINE = range(FINAL - 4, FINAL)  # the 4 weeks before the final week
POS_CHARGE = 0.005  # flat in every week, so pos_charge_rise is always a red herring

SCENARIOS = {
    "s01": {  # demo: four causes at once
        "seed": 101, "steady": True,
        "causes": ["supplier_cost_rise", "promo_overrun", "wastage_spike", "transfer_leakage"],
        "red_herrings": ["pos_charge_rise"],
    },
    # Every scenario is steady: only the planted causes change the final week.
    "s02": {"seed": 202, "steady": True, "causes": ["supplier_cost_rise"], "red_herrings": ["pos_charge_rise"]},
    "s03": {"seed": 303, "steady": True, "causes": ["promo_overrun", "wastage_spike"], "red_herrings": ["pos_charge_rise"]},
    # "Sales fell" is plausible but false: sales hold steady while transfers go missing.
    "s04": {"seed": 404, "steady": True, "causes": ["transfer_leakage"],
            "red_herrings": ["sales_volume_drop", "pos_charge_rise"]},
    "s05": {"seed": 505, "steady": True, "causes": [], "red_herrings": ["pos_charge_rise"]},  # no planted cause
}

# name, category, unit, list price (NGN), perishable, popularity weight
PRODUCTS = [
    ("Peak Milk 400g", "dairy", "tin", 1650, False, 9),
    ("Peak Milk 16g sachet", "dairy", "sachet", 150, False, 8),
    ("Three Crowns Milk 400g", "dairy", "tin", 1450, False, 4),
    ("Hollandia Yoghurt 1L", "dairy", "bottle", 2400, True, 5),
    ("Indomie Chicken 70g", "noodles", "pack", 250, False, 10),
    ("Indomie Onion 70g", "noodles", "pack", 250, False, 6),
    ("Golden Penny Spaghetti 500g", "pasta", "pack", 1100, False, 6),
    ("Golden Penny Semovita 1kg", "flour", "bag", 1700, False, 5),
    ("Dangote Sugar 500g", "sugar", "pack", 900, False, 6),
    ("St Louis Sugar Cubes", "sugar", "box", 1300, False, 3),
    ("Mama Gold Rice 5kg", "rice", "bag", 9800, False, 3),
    ("Royal Stallion Rice 1kg", "rice", "bag", 2100, False, 4),
    ("Kings Vegetable Oil 1L", "oil", "bottle", 2900, False, 4),
    ("Power Oil 75cl", "oil", "bottle", 2300, False, 3),
    ("Gino Tomato Paste 70g", "paste", "sachet", 200, False, 7),
    ("Maggi Star Cube", "seasoning", "pack", 50, False, 9),
    ("Knorr Chicken Cube", "seasoning", "pack", 60, False, 6),
    ("Dano Milk Powder 400g", "dairy", "pack", 3200, False, 3),
    ("Milo 400g", "beverage", "tin", 3500, False, 4),
    ("Bournvita 500g", "beverage", "tin", 3900, False, 3),
    ("Lipton Tea 50 bags", "beverage", "box", 1500, False, 3),
    ("Nescafe Classic 50g", "beverage", "jar", 2200, False, 2),
    ("Coca-Cola 50cl", "drinks", "bottle", 400, False, 9),
    ("Fanta 50cl", "drinks", "bottle", 400, False, 6),
    ("Malta Guinness 33cl", "drinks", "can", 600, False, 6),
    ("Eva Water 75cl", "drinks", "bottle", 250, False, 8),
    ("Chi Exotic Juice 1L", "drinks", "pack", 1800, True, 3),
    ("Agege Bread", "bakery", "loaf", 1200, True, 7),
    ("Butterfield Bread", "bakery", "loaf", 1500, True, 5),
    ("Eggs (crate of 30)", "eggs", "crate", 5200, True, 4),
    ("Gala Sausage Roll", "snacks", "pack", 300, True, 7),
    ("Digestive Biscuits", "snacks", "pack", 700, False, 4),
    ("Cabin Biscuits", "snacks", "pack", 350, False, 5),
    ("Plantain Chips", "snacks", "pack", 300, False, 4),
    ("Hypo Bleach 1L", "household", "bottle", 900, False, 2),
    ("Ariel Detergent 500g", "household", "pack", 1600, False, 3),
    ("Morning Fresh 400ml", "household", "bottle", 1400, False, 2),
    ("Joy Soap", "toiletries", "bar", 450, False, 3),
    ("Closeup Toothpaste 140g", "toiletries", "tube", 1300, False, 2),
    ("Always Pads", "toiletries", "pack", 1200, False, 2),
]
SUPPLIERS = {"SUP1": "Lagos Provisions Ltd", "SUP2": "Ikeja Wholesale Depot", "SUP3": "Mushin Fresh Foods"}
STAFF = [("ST01", "Tunde", "cashier"), ("ST02", "Amaka", "cashier")]

# Planted cause details for the final week.
COST_RISE_PRODUCT = "P001"  # Peak Milk 400g
COST_RISE_PCT = 0.40
PROMO_PRODUCT = "P019"  # Milo 400g
PROMO_PCT = 15
LEAKY_STAFF = "ST01"
LEAKED_TRANSFERS = 6

# Monthly costs, each paid with a cover period of the calendar month it pays for.
RENT_NGN = 150000
SALARIES_NGN = {"ST01": 85000, "ST02": 80000}
LEVY_NGN = 5000


def day(d: int) -> date:
    return START + timedelta(days=d)


def week_of(d: date) -> int:
    return (d - START).days // 7


def ngn(value: float) -> str:
    return f"{value:.2f}"


def supplier_for(category: str) -> str:
    if category in ("dairy", "bakery", "eggs"):
        return "SUP3"
    return "SUP1" if category in ("noodles", "pasta", "flour", "sugar", "rice", "oil", "paste", "seasoning") else "SUP2"


def generate(scenario: str, out: Path) -> dict:
    spec = SCENARIOS[scenario]
    causes = set(spec["causes"])
    rng = random.Random(spec["seed"])
    tables: dict[str, list[dict]] = {name: [] for name in (
        "products", "staff", "sales", "sale_lines", "promos", "stock_movements",
        "bank_statement", "supplier_invoices", "expenses", "fx_rates", "calendar")}

    products = []
    for i, (name, category, unit, price, perishable, weight) in enumerate(PRODUCTS, start=1):
        pid = f"P{i:03d}"
        cost = round(price * (0.72 if category in ("drinks", "snacks") else 0.8))
        products.append({"product_id": pid, "name": name, "category": category, "price": price,
                         "perishable": perishable, "weight": weight, "cost": cost})
        tables["products"].append({"product_id": pid, "sku": f"SKU-{i:04d}", "name": name, "category": category,
                                   "unit": unit, "list_price_ngn": ngn(price), "is_perishable": str(perishable).lower()})
    by_id = {p["product_id"]: p for p in products}
    for sid, name, role in STAFF:
        tables["staff"].append({"staff_id": sid, "name": name, "role": role})

    # Promo runs one week well before the baseline; with promo_overrun the till keeps applying it in the final week.
    promo_start, promo_end = day(7 * (FINAL - 6)), day(7 * (FINAL - 5) - 1)
    tables["promos"].append({"promo_id": "PR01", "product_id": PROMO_PRODUCT, "pct_off": PROMO_PCT,
                             "start_date": promo_start.isoformat(), "end_date": promo_end.isoformat()})

    # The supplier cost rise lands on one invoice early in the final week; sales before it keep the old cost.
    deliveries = random.Random(spec["seed"] * 3 + 1)
    rise_day = day(7 * FINAL + deliveries.randint(0, 2))

    def unit_cost(pid: str, on: date) -> int:
        """The clean ledger's cost in force on a day: the latest invoice on or before it."""
        base = by_id[pid]["cost"]
        if pid == COST_RISE_PRODUCT and "supplier_cost_rise" in causes and on >= rise_day:
            return round(base * (1 + COST_RISE_PCT))
        return base

    # Opening stock is invoiced on the first day; after that perishables come 2 to 3 times a week, fast
    # movers 1 to 2 times, and slow movers once a fortnight, each on varying weekdays.
    schedule: list[tuple[date, dict]] = [(START, p) for p in products]
    for week in range(WEEKS):
        for p in products:
            if p["perishable"]:
                count = deliveries.randint(2, 3)
            elif p["weight"] >= 6:
                count = deliveries.randint(1, 2)
            else:
                count = week % 2
            days = {day(7 * week + d) for d in deliveries.sample(range(7), count)} - {START}
            if p["product_id"] == COST_RISE_PRODUCT and week == FINAL and "supplier_cost_rise" in causes:
                days = {d for d in days if d > rise_day} | {rise_day}
            schedule += [(d, p) for d in sorted(days)]
    schedule.sort(key=lambda item: (item[0], item[1]["product_id"]))
    for inv, (when, p) in enumerate(schedule, start=1):
        qty = deliveries.choice((20, 24, 30)) if p["perishable"] else (60 if p["weight"] >= 6 else 30)
        cost = unit_cost(p["product_id"], when)
        sup = supplier_for(p["category"])
        tables["supplier_invoices"].append({
            "invoice_id": f"INV-{inv:05d}", "invoice_date": when.isoformat(), "supplier_id": sup,
            "supplier_name": SUPPLIERS[sup], "product_id": p["product_id"], "qty": qty,
            "unit_cost_ngn": ngn(cost), "total_ngn": ngn(qty * cost)})

    sale_no = line_no = txn = mov = 0
    weights = [p["weight"] for p in products]
    leak_refs: list[tuple[str, float]] = []
    for d in range(WEEKS * 7):
        today = day(d)
        week = week_of(today)
        settle_pos = cash_total = 0.0
        # Steady scenarios replay the same customers on each weekday, so only the planted causes move the week.
        shop = random.Random(spec["seed"] * 10 + today.weekday()) if spec.get("steady") else rng
        for _ in range(shop.randint(50, 70)):
            sale_no += 1
            sale_id = f"SL-{sale_no:05d}"
            staff_id = STAFF[shop.randrange(2)][0]
            method = shop.choices(["cash", "transfer", "pos_card"], [45, 35, 20])[0]
            sold_at = datetime.combine(today, datetime.min.time()) + timedelta(minutes=shop.randint(8 * 60, 20 * 60))
            gross = discount = 0.0
            # dict.fromkeys dedupes in draw order; a set would vary with hash seeding.
            for pid in dict.fromkeys(p["product_id"] for p in shop.choices(products, weights, k=shop.randint(1, 4))):
                line_no += 1
                qty = shop.randint(1, 3)
                price = by_id[pid]["price"]
                promo = pid == PROMO_PRODUCT and (promo_start <= today <= promo_end or (
                    week == FINAL and "promo_overrun" in causes))
                line_discount = round(qty * price * PROMO_PCT / 100) if promo else 0
                gross += qty * price
                discount += line_discount
                tables["sale_lines"].append({
                    "line_id": f"LN-{line_no:06d}", "sale_id": sale_id, "product_id": pid, "qty": qty,
                    "unit_price_ngn": ngn(price), "discount_ngn": ngn(line_discount), "promo_id": "PR01" if promo else ""})
            net = gross - discount
            ref = f"TRF{sale_no:06d}" if method == "transfer" else ""
            tables["sales"].append({
                "sale_id": sale_id, "sold_at": sold_at.isoformat(sep=" "), "staff_id": staff_id,
                "payment_method": method, "transfer_ref": ref, "gross_ngn": ngn(gross),
                "discount_ngn": ngn(discount), "net_ngn": ngn(net)})
            if method == "transfer":
                leak = (week == FINAL and "transfer_leakage" in causes and staff_id == LEAKY_STAFF
                        and len(leak_refs) < min(LEAKED_TRANSFERS, today.weekday() + 1) and rng.random() < 0.3)
                if leak:
                    leak_refs.append((sale_id, net))
                else:
                    txn += 1
                    posted = sold_at + timedelta(hours=rng.randint(0, 36))
                    tables["bank_statement"].append({
                        "txn_id": f"TX-{txn:06d}", "posted_at": posted.isoformat(sep=" "), "direction": "credit",
                        "amount_ngn": ngn(net), "channel": "transfer", "ref": ref,
                        "counterparty": f"Customer {rng.randint(100, 999)}", "narration": f"Transfer {ref}"})
            elif method == "pos_card":
                settle_pos += net
            else:
                cash_total += net

        next_morning = datetime.combine(today + timedelta(days=1), datetime.min.time()) + timedelta(hours=9)
        if settle_pos:
            charge = round(settle_pos * POS_CHARGE, 2)
            for amount, direction, channel, narration in (
                    (settle_pos, "credit", "pos_settlement", "POS settlement"),
                    (charge, "debit", "charge", "POS terminal charge")):
                txn += 1
                tables["bank_statement"].append({
                    "txn_id": f"TX-{txn:06d}", "posted_at": next_morning.isoformat(sep=" "), "direction": direction,
                    "amount_ngn": ngn(amount), "channel": channel, "ref": f"POS-{today:%Y%m%d}",
                    "counterparty": "Moniepoint", "narration": f"{narration} {today.isoformat()}"})
        if cash_total:
            txn += 1
            tables["bank_statement"].append({
                "txn_id": f"TX-{txn:06d}", "posted_at": next_morning.isoformat(sep=" "), "direction": "credit",
                "amount_ngn": ngn(cash_total), "channel": "cash_deposit", "ref": f"CASH-{today:%Y%m%d}",
                "counterparty": "Self", "narration": "Cash deposit"})

        # Expired or damaged perishables, counted at closing.
        for p in products:
            if not p["perishable"]:
                continue
            qty = shop.choice((0, 0, 0, 1))
            if week == FINAL and "wastage_spike" in causes:
                qty += rng.randint(0, 1)
            if qty:
                mov += 1
                tables["stock_movements"].append({
                    "movement_id": f"MV-{mov:05d}", "product_id": p["product_id"],
                    "moved_at": f"{today.isoformat()} 21:00:00", "qty": qty,
                    "type": rng.choice(["expired", "damaged"]), "unit_cost_ngn": ngn(unit_cost(p["product_id"], today)),
                    "note": "closing count"})

        tables["fx_rates"].append({"date": today.isoformat(),
                                   "usd_ngn": ngn(1530 + d * 0.4 + (60 if week == FINAL else 0))})
        tables["calendar"].append({"cal_date": today.isoformat()})

    for invoice in tables["supplier_invoices"]:
        mov += 1
        tables["stock_movements"].append({
            "movement_id": f"MV-{mov:05d}", "product_id": invoice["product_id"],
            "moved_at": f"{invoice['invoice_date']} 08:00:00", "qty": invoice["qty"], "type": "receive",
            "unit_cost_ngn": invoice["unit_cost_ngn"], "note": "delivery"})
    tables["expenses"] = expenses(spec)

    out.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with (out / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    key = answer_key(scenario, tables, promo_end, leak_refs, unit_cost)
    (out / "answer_key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    return key


def month_end(first: date) -> date:
    return (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)


def expenses(spec: dict) -> list[dict]:
    """The expense book. Monthly items carry a cover period; day-to-day spend leaves it empty.

    Day-to-day spend repeats one weekly pattern of days and amounts, so it never hides or fakes a planted cause.
    """
    spend = random.Random(spec["seed"] * 7 + 5)
    rows: list[tuple] = []  # (date, category, amount, cover_start, cover_end, note)
    first = START
    while first <= day(7 * WEEKS - 1):
        last = month_end(first)
        rows.append((first, "rent", RENT_NGN, first, last, f"shop rent {first:%b %Y}"))
        for staff_id, name, _ in STAFF:  # paid in the first days of the month it covers
            rows.append((first + timedelta(days=spend.randint(0, 2)), "salary", SALARIES_NGN[staff_id],
                         first, last, f"{name} {first:%b} salary"))
        rows.append((first + timedelta(days=spend.randint(2, 6)), "levy", LEVY_NGN, first, last, f"LAWMA {first:%b %Y}"))
        first = last + timedelta(days=1)

    def week_pattern(r: random.Random) -> list[tuple]:
        pattern = [(d, "diesel", 20 * r.choice(range(1950, 2151, 50)), "diesel 20 litres")
                   for d in r.sample(range(7), r.randint(2, 4))]
        return pattern + [(d, "transport", r.choice(range(1500, 6001, 500)), "transport to market")
                          for d in r.sample(range(7), r.randint(2, 5))]

    pattern = week_pattern(random.Random(spec["seed"] * 7 + 6))
    for week in range(WEEKS):
        for d, category, amount, note in pattern:
            rows.append((day(7 * week + d), category, amount, None, None, note))
        rows.append((day(7 * week + 3), "electricity", 12000, None, None, "prepaid meter token"))
    rows.sort(key=lambda r: (r[0], r[1], r[5]))
    return [{"expense_id": f"EX-{i:04d}", "expense_date": when.isoformat(), "category": category,
             "amount_ngn": ngn(amount), "cover_start": start.isoformat() if start else "",
             "cover_end": end.isoformat() if end else "", "note": note}
            for i, (when, category, amount, start, end, note) in enumerate(rows, start=1)]


def answer_key(scenario: str, tables: dict, promo_end: date, leak_refs: list, unit_cost) -> dict:
    """Each impact is the profit effect in the final week, defined by the query the agent should run."""
    final = lambda iso: week_of(date.fromisoformat(iso[:10])) == FINAL  # noqa: E731
    base_weeks = lambda iso: week_of(date.fromisoformat(iso[:10])) in BASELINE  # noqa: E731
    causes = set(SCENARIOS[scenario]["causes"])
    impacts: dict[str, float] = {}

    if "supplier_cost_rise" in causes:
        # Units sold in the final week at the cost in force on their day, against the baseline's average
        # cost in force per unit sold.
        sold_on = {s["sale_id"]: s["sold_at"][:10] for s in tables["sales"]}
        lines = [(sold_on[l["sale_id"]], l["qty"]) for l in tables["sale_lines"] if l["product_id"] == COST_RISE_PRODUCT]
        cost = lambda keep: sum(q * unit_cost(COST_RISE_PRODUCT, date.fromisoformat(d))  # noqa: E731
                                for d, q in lines if keep(d))
        units = lambda keep: sum(q for d, q in lines if keep(d))  # noqa: E731
        impacts["supplier_cost_rise"] = -(cost(final) - units(final) * cost(base_weeks) / units(base_weeks))
    if "promo_overrun" in causes:
        sold_on = {s["sale_id"]: s["sold_at"] for s in tables["sales"]}
        impacts["promo_overrun"] = -sum(float(l["discount_ngn"]) for l in tables["sale_lines"]
                                        if l["promo_id"] and date.fromisoformat(sold_on[l["sale_id"]][:10]) > promo_end)
    if "wastage_spike" in causes:
        value = lambda keep: sum(m["qty"] * float(m["unit_cost_ngn"]) for m in tables["stock_movements"]  # noqa: E731
                                 if m["type"] in ("expired", "damaged") and keep(m["moved_at"]))
        impacts["wastage_spike"] = -(value(final) - value(base_weeks) / len(BASELINE))
    if "transfer_leakage" in causes:
        impacts["transfer_leakage"] = -sum(net for _, net in leak_refs)

    ranked = sorted(impacts, key=lambda c: impacts[c])
    return {
        "scenario": scenario,
        "synthetic": True,
        "final_week": {"start": day(7 * FINAL).isoformat(), "end": day(7 * WEEKS - 1).isoformat()},
        "baseline_weeks": {"start": day(7 * BASELINE[0]).isoformat(), "end": day(7 * FINAL - 1).isoformat()},
        "history": {"start": START.isoformat(), "end": day(7 * WEEKS - 1).isoformat()},
        "accrual": "an expense with cover_start and cover_end is spread evenly per day over that period",
        "cost_rule": "a sale line is costed at the latest supplier invoice for its product on or before the sale day",
        "causes": [{"cause_id": c, "impact_ngn": round(impacts[c], 2), "rank": i + 1} for i, c in enumerate(ranked)],
        "red_herrings": SCENARIOS[scenario]["red_herrings"],
        "leaked_sale_ids": [sale_id for sale_id, _ in leak_refs],
        "tolerance_pct": 10,
    }


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "s01"
    print(json.dumps(generate(name, ROOT / name), indent=2))
