"""Checks that prove a mapping before any investigation runs. A failed check blocks the mapping."""
from __future__ import annotations

from collections import defaultdict

from .mapping import ROLES

SHARE = 0.99  # share of records that must agree, so one odd record never blocks an upload
TOLERANCE = 1.0  # naira


def _check(name: str, ok: bool, detail: str) -> dict:
    return {"check": name, "ok": bool(ok), "detail": detail}


def _share(name: str, hits: int, total: int, what: str, need: float = SHARE) -> dict:
    share = hits / total if total else 1.0
    return _check(name, share >= need, f"{hits} of {total} {what} ({share:.1%}, need {need:.0%})")


def check(mapping: dict, tables: dict[str, list[dict]], errors: list[str]) -> list[dict]:
    roles = mapping["roles"]
    out = [_check("sales found", "sale" in roles and bool(tables["sales"]), "a sales file with records is needed"),
           _check("values read cleanly", not errors, "; ".join(errors) or "every date, number and yes/no read")]
    payments = roles.get("sale", {}).get("value_maps", {}).get("payment_method", {})
    unknown = [v for v, c in payments.items() if c is None]
    out.append(_check("sale: payment types recognised", not unknown,
                      f"We don't recognise these payment types: {', '.join(unknown)}" if unknown
                      else "every payment type has a known meaning"))
    for role, entry in roles.items():
        spec = ROLES[role]
        rows = tables[spec["table"]]
        blank = [f for f in spec["required"] if any(r[f] is None for r in rows)]
        out.append(_check(f"{role}: required fields filled", not blank,
                          f"blank values in {blank}" if blank else f"{len(rows)} rows"))
        keys = [r[spec["key"]] for r in rows]
        repeats = len(keys) - len(set(keys))
        out.append(_check(f"{role}: ids unique", not repeats,
                          f"{repeats} repeated values in '{entry['columns'][spec['key']]}'" if repeats else f"{len(keys)} ids"))

    sales, lines = tables["sales"], tables["sale_lines"]
    if "gross_ngn" in roles.get("sale", {}).get("columns", {}):
        hits = sum(abs(s["gross_ngn"] - (s["discount_ngn"] or 0) - s["net_ngn"]) <= TOLERANCE for s in sales
                   if None not in (s["gross_ngn"], s["net_ngn"]))
        out.append(_share("sale: gross minus discount equals net", hits, len(sales), "sales"))
    if sales and lines:
        net = {s["sale_id"]: s["net_ngn"] for s in sales}
        out.append(_share("sale_line: every line points at a sale",
                          sum(l["sale_id"] in net for l in lines), len(lines), "lines"))
        total: dict = defaultdict(float)
        for l in lines:
            total[l["sale_id"]] += (l["qty"] or 0) * (l["unit_price_ngn"] or 0) - (l["discount_ngn"] or 0)
        hits = sum(n is not None and abs(total.get(i, 0) - n) <= TOLERANCE for i, n in net.items())
        out.append(_share("sale_line: lines add up to each sale's net amount", hits, len(sales), "sales"))
    if lines and tables["products"]:
        known = {p["product_id"] for p in tables["products"]}
        out.append(_share("sale_line: products are in the product list",
                          sum(l["product_id"] in known for l in lines), len(lines), "lines"))
    invoices = [i for i in tables["supplier_invoices"] if None not in (i["qty"], i["unit_cost_ngn"], i["total_ngn"])]
    if invoices and "total_ngn" in roles["cost"]["columns"]:
        hits = sum(abs(i["qty"] * i["unit_cost_ngn"] - i["total_ngn"]) <= TOLERANCE for i in invoices)
        out.append(_share("cost: quantity times unit cost equals invoice total", hits, len(invoices), "invoice rows"))
    transfers = [s for s in sales if s["payment_method"] == "transfer"]
    if transfers and tables["bank_statement"]:
        credits = {(b["ref"], b["amount_ngn"]) for b in tables["bank_statement"] if b["direction"] == "credit"}
        hits = sum((s["transfer_ref"], s["net_ngn"]) in credits for s in transfers)
        # Some transfers never arrive (that is a cause Becuz looks for), so most, not all, must match.
        out.append(_share("bank_txn: most transfer sales find a bank credit with the same ref and amount",
                          hits, len(transfers), "transfer sales", need=0.5))
    return out
