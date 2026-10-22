"""Seeded synthetic shop generator: 8 weeks of records for one Nigerian mini-mart.

Writes one CSV per table plus answer_key.json into data/scenarios/<scenario>/.
All data is synthetic. Causes are planted only in the final week.

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
START = date(2026, 8, 24)  # a Monday; 8 weeks, the last week is the one investigated
WEEKS = 8
FINAL = WEEKS - 1
BASELINE = range(FINAL - 4, FINAL)  # the 4 weeks before the final week
POS_CHARGE = 0.005  # flat in every week, so pos_charge_rise is always a red herring

SCENARIOS = {
    "s01": {
        "seed": 101,
        "causes": ["supplier_cost_rise", "promo_overrun", "wastage_spike", "transfer_leakage"],
        "red_herrings": ["pos_charge_rise"],
    },
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
        "bank_statement", "supplier_invoices", "expenses", "fx_rates")}

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

    # Promo runs one baseline week; with promo_overrun the till keeps applying it in the final week.
    promo_start, promo_end = day(7 * (FINAL - 1)), day(7 * FINAL - 1)
    tables["promos"].append({"promo_id": "PR01", "product_id": PROMO_PRODUCT, "pct_off": PROMO_PCT,
                             "start_date": promo_start.isoformat(), "end_date": promo_end.isoformat()})

    def unit_cost(pid: str, week: int) -> int:
        base = by_id[pid]["cost"]
        if pid == COST_RISE_PRODUCT and week == FINAL and "supplier_cost_rise" in causes:
            return round(base * (1 + COST_RISE_PCT))
        return base

    # Weekly supplier invoices and stock receipts, every Monday.
    inv = 0
    for week in range(WEEKS):
        monday = day(7 * week)
        for p in products:
            inv += 1
            qty = 60 if p["weight"] >= 6 else 30
            cost = unit_cost(p["product_id"], week)
            sup = supplier_for(p["category"])
            tables["supplier_invoices"].append({
                "invoice_id": f"INV-{inv:04d}", "invoice_date": monday.isoformat(), "supplier_id": sup,
                "supplier_name": SUPPLIERS[sup], "product_id": p["product_id"], "qty": qty,
                "unit_cost_ngn": ngn(cost), "total_ngn": ngn(qty * cost)})

    sale_no = line_no = txn = mov = 0
    weights = [p["weight"] for p in products]
    leak_refs: list[tuple[str, float]] = []
    for d in range(WEEKS * 7):
        today = day(d)
        week = week_of(today)
        settle_pos = cash_total = 0.0
        for _ in range(rng.randint(50, 70)):
            sale_no += 1
            sale_id = f"SL-{sale_no:05d}"
            staff_id = STAFF[rng.randrange(2)][0]
            method = rng.choices(["cash", "transfer", "pos_card"], [45, 35, 20])[0]
            sold_at = datetime.combine(today, datetime.min.time()) + timedelta(minutes=rng.randint(8 * 60, 20 * 60))
            gross = discount = 0.0
            # dict.fromkeys dedupes in draw order; a set would vary with hash seeding.
            for pid in dict.fromkeys(p["product_id"] for p in rng.choices(products, weights, k=rng.randint(1, 4))):
                line_no += 1
                qty = rng.randint(1, 3)
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
                        and len(leak_refs) < LEAKED_TRANSFERS and rng.random() < 0.3)
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
            qty = rng.choice((0, 0, 0, 1))
            if week == FINAL and "wastage_spike" in causes:
                qty += rng.randint(0, 1)
            if qty:
                mov += 1
                tables["stock_movements"].append({
                    "movement_id": f"MV-{mov:05d}", "product_id": p["product_id"],
                    "moved_at": f"{today.isoformat()} 21:00:00", "qty": qty,
                    "type": rng.choice(["expired", "damaged"]), "unit_cost_ngn": ngn(unit_cost(p["product_id"], week)),
                    "note": "closing count"})

        tables["fx_rates"].append({"date": today.isoformat(),
                                   "usd_ngn": ngn(1530 + d * 0.4 + (60 if week == FINAL else 0))})

    for week in range(WEEKS):
        monday = day(7 * week)
        for p in products:
            mov += 1
            tables["stock_movements"].append({
                "movement_id": f"MV-{mov:05d}", "product_id": p["product_id"], "moved_at": f"{monday.isoformat()} 08:00:00",
                "qty": 60 if p["weight"] >= 6 else 30, "type": "receive",
                "unit_cost_ngn": ngn(unit_cost(p["product_id"], week)), "note": "weekly delivery"})
        for i, (category, amount) in enumerate((("diesel", 42000), ("transport", 15000), ("salary", 70000),
                                                ("rent", 30000), ("levy", 5000))):
            tables["expenses"].append({"expense_id": f"EX-{week:02d}{i}", "expense_date": monday.isoformat(),
                                       "category": category, "amount_ngn": ngn(amount), "note": "weekly"})

    out.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with (out / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    key = answer_key(scenario, tables, promo_end, leak_refs)
    (out / "answer_key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    return key


def answer_key(scenario: str, tables: dict, promo_end: date, leak_refs: list) -> dict:
    """Each impact is the profit effect in the final week, defined by the query the agent should run."""
    final = lambda iso: week_of(date.fromisoformat(iso[:10])) == FINAL  # noqa: E731
    base_weeks = lambda iso: week_of(date.fromisoformat(iso[:10])) in BASELINE  # noqa: E731
    causes = set(SCENARIOS[scenario]["causes"])
    impacts: dict[str, float] = {}

    if "supplier_cost_rise" in causes:
        cost = {w: float(r["unit_cost_ngn"]) for r in tables["supplier_invoices"]
                if r["product_id"] == COST_RISE_PRODUCT for w in [week_of(date.fromisoformat(r["invoice_date"]))]}
        sold_on = {s["sale_id"]: s["sold_at"] for s in tables["sales"]}
        qty = sum(l["qty"] for l in tables["sale_lines"]
                  if l["product_id"] == COST_RISE_PRODUCT and final(sold_on[l["sale_id"]]))
        base_cost = sum(cost[w] for w in BASELINE) / len(BASELINE)
        impacts["supplier_cost_rise"] = -qty * (cost[FINAL] - base_cost)
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
        "causes": [{"cause_id": c, "impact_ngn": round(impacts[c], 2), "rank": i + 1} for i, c in enumerate(ranked)],
        "red_herrings": SCENARIOS[scenario]["red_herrings"],
        "leaked_sale_ids": [sale_id for sale_id, _ in leak_refs],
        "tolerance_pct": 10,
    }


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "s01"
    print(json.dumps(generate(name, ROOT / name), indent=2))
