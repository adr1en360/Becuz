"""Deterministic mapping of uploaded CSVs onto Becuz's canonical roles. No model is involved.

A role is one logical table. Its fields are the canonical columns (same names and order as
data/scenarios/s01/<table>.csv), each with a kind and header synonyms. Files are matched to roles
by header synonyms, column types and key uniqueness; value columns (payment method, movement type,
bank channel) are also matched by their values and get a value map onto the canonical vocabulary.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

from .profile import BOOLS, parse_date, parse_number, read_csv

F = dict  # field -> (kind, synonyms); the field's own name is always the first synonym
ROLES: dict[str, dict] = {
    "sale": {"table": "sales", "key": "sale_id", "required": ["sale_id", "sold_at", "net_ngn"],
             "files": ["sales", "sale", "transactions", "receipts", "orders"], "fields": F(
        sale_id=("id", ["txn ref", "transaction id", "transaction ref", "receipt no", "receipt number", "order id"]),
        sold_at=("ts", ["date time", "sale date", "transaction date", "timestamp", "date"]),
        staff_id=("id", ["cashier", "staff", "cashier id", "served by", "attendant"]),
        payment_method=("value", ["paid via", "payment", "payment type", "tender", "mode of payment", "method"]),
        transfer_ref=("id", ["transfer no", "transfer reference", "bank ref", "transfer id"]),
        gross_ngn=("money", ["gross", "subtotal", "sub total", "gross amount"]),
        discount_ngn=("money", ["discount", "disc", "discount amount"]),
        net_ngn=("money", ["net", "amount paid", "total paid", "net amount", "amount", "total"]),
    )},
    "sale_line": {"table": "sale_lines", "key": "line_id", "required": ["line_id", "sale_id", "product_id", "qty"],
                  "files": ["lines", "items sold", "sale lines", "line items", "basket"], "fields": F(
        line_id=("id", ["item row", "line no", "line number", "row id"]),
        sale_id=("id", ["txn ref", "transaction id", "receipt no", "order id"]),
        product_id=("id", ["item code", "product code", "item id", "sku"]),
        qty=("int", ["quantity", "units", "count"]),
        unit_price_ngn=("money", ["unit price", "price", "selling price"]),
        discount_ngn=("money", ["item discount", "discount", "disc"]),
        promo_id=("id", ["promo code", "promo", "promotion"]),
    )},
    "product": {"table": "products", "key": "product_id", "required": ["product_id"],
                "files": ["products", "items", "catalogue", "catalog", "inventory list"], "fields": F(
        product_id=("id", ["item code", "product code", "item id", "code"]),
        sku=("id", ["barcode"]),
        name=("text", ["description", "item name", "product name", "product"]),
        category=("text", ["group", "department", "item group"]),
        unit=("text", ["uom", "pack"]),
        list_price_ngn=("money", ["list price", "price", "selling price", "retail price"]),
        is_perishable=("bool", ["perishable"]),
    )},
    "cost": {"table": "supplier_invoices", "key": "invoice_id",
             "required": ["invoice_id", "invoice_date", "product_id", "unit_cost_ngn"],
             "files": ["supplier invoices", "purchases", "invoices", "bills", "supplies"], "fields": F(
        invoice_id=("id", ["invoice no", "invoice number", "bill no"]),
        invoice_date=("date", ["bill date", "purchase date", "date"]),
        supplier_id=("id", ["supplier code", "vendor id"]),
        supplier_name=("text", ["supplier", "vendor"]),
        product_id=("id", ["item code", "product code", "item id", "sku"]),
        qty=("int", ["quantity", "units"]),
        unit_cost_ngn=("money", ["unit cost", "cost price", "cost"]),
        total_ngn=("money", ["line total", "total cost", "total", "amount"]),
    )},
    "expense": {"table": "expense_book", "key": "expense_id", "required": ["expense_id", "expense_date", "amount_ngn"],
                "files": ["expenses", "spending", "costs", "overheads"], "fields": F(
        expense_id=("id", ["ref", "reference", "voucher no"]),
        expense_date=("date", ["paid on", "payment date", "date"]),
        category=("text", ["type", "expense type", "head"]),
        amount_ngn=("money", ["amount", "amount paid", "cost", "value"]),
        cover_start=("date", ["period start", "covers from", "cover from"]),
        cover_end=("date", ["period end", "covers to", "cover to"]),
        note=("text", ["memo", "description", "narration", "remarks"]),
    )},
    "stock_movement": {"table": "stock_movements", "key": "movement_id",
                       "required": ["movement_id", "product_id", "moved_at", "qty", "type"],
                       "files": ["stock", "stock movements", "inventory", "movements"], "fields": F(
        movement_id=("id", ["movement no", "stock ref"]),
        product_id=("id", ["item code", "product code", "item id", "sku"]),
        moved_at=("ts", ["movement date", "date"]),
        qty=("int", ["quantity", "units"]),
        type=("value", ["movement type", "reason", "movement"]),
        unit_cost_ngn=("money", ["unit cost", "cost price", "cost"]),
        note=("text", ["memo", "remarks", "comment"]),
    )},
    "bank_txn": {"table": "bank_statement", "key": "txn_id", "required": ["txn_id", "posted_at"],
                 "any_of": [["amount_ngn", "direction"], ["debit_ngn", "credit_ngn"]],
                 "files": ["bank", "bank statement", "statement"], "fields": F(
        txn_id=("id", ["tran id", "transaction id", "txn no"]),
        posted_at=("ts", ["txn date", "trans date", "transaction date", "posting date", "value date", "date"]),
        direction=("value", ["dr cr", "debit credit"]),
        amount_ngn=("money", ["amount"]),
        channel=("value", ["channel type", "category"]),
        ref=("id", ["reference", "session id"]),
        counterparty=("text", ["beneficiary", "sender", "party"]),
        narration=("text", ["description", "details", "remarks"]),
        debit_ngn=("money", ["debit", "withdrawal", "money out", "dr"]),  # input only, folded into amount
        credit_ngn=("money", ["credit", "deposit", "lodgement", "money in", "cr"]),
    )},
    "promo": {"table": "promos", "key": "promo_id", "required": ["promo_id", "end_date"],
              "files": ["promos", "promotions", "discounts", "offers"], "fields": F(
        promo_id=("id", ["promo code", "promotion id", "code"]),
        product_id=("id", ["item code", "product code", "item id", "sku"]),
        pct_off=("int", ["percent off", "discount pct", "discount", "off"]),
        start_date=("date", ["starts", "start", "from"]),
        end_date=("date", ["ends", "end", "until", "to"]),
    )},
    # Support tables: not roles of their own, but the canonical USL needs them.
    "staff": {"table": "staff", "key": "staff_id", "required": ["staff_id"], "support": True,
              "files": ["staff", "team", "employees", "cashiers"], "fields": F(
        staff_id=("id", ["staff code", "cashier", "employee id", "code"]),
        name=("text", ["full name", "staff name"]),
        role=("text", ["position", "title", "job"]),
    )},
    "fx": {"table": "fx_rates", "key": "date", "required": ["date", "usd_ngn"], "support": True,
           "files": ["fx", "rates", "fx rates", "exchange rates"], "fields": F(
        date=("date", ["day", "rate date"]),
        usd_ngn=("money", ["usd rate", "rate", "usd"]),
    )},
}
INPUT_ONLY = {"debit_ngn", "credit_ngn"}

# Canonical vocabularies, checked in order; a source value maps to the first one whose synonym tokens it holds.
VALUE_MAPS = {
    ("sale", "payment_method"): {"transfer": ["transfer", "trf", "nip"], "pos_card": ["pos", "card", "atm"],
                                 "cash": ["cash"]},
    ("stock_movement", "type"): {"expired": ["expired", "expiry", "spoilt", "spoiled", "rotten"],
                                 "damaged": ["damaged", "damage", "broken", "breakage"],
                                 "receive": ["receive", "received", "delivery", "restock"]},
    ("bank_txn", "channel"): {"charge": ["charge", "charges", "fee", "fees", "commission", "stamp duty"],
                              "pos_settlement": ["pos settlement", "settlement", "pos"],
                              "cash_deposit": ["cash deposit", "deposit"], "transfer": ["transfer", "nip", "trf"]},
    ("bank_txn", "direction"): {"credit": ["credit", "cr"], "debit": ["debit", "dr"]},
}
LOSS_TYPES = ["expired", "damaged"]
MISSING_REASON = {
    "sale": "your upload has no sales records", "sale_line": "your upload has no sale line items",
    "product": "your upload has no product list", "cost": "your upload has no supplier invoices",
    "expense": "your upload has no expenses", "stock_movement": "your upload has no stock records",
    "bank_txn": "your upload has no bank statement", "promo": "your upload has no promotions",
}
CURRENCY = {"ngn", "naira"}
TYPES = {"id": {"text", "int"}, "text": {"text", "int", "number", "bool", "date"}, "value": {"text"},
         "money": {"int", "number"}, "int": {"int"}, "date": {"date"}, "ts": {"date"}, "bool": {"bool", "text"}}


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in CURRENCY]


def columns_of(table: str) -> list[str]:
    if table == "calendar":
        return ["cal_date"]
    role = next(r for r in ROLES.values() if r["table"] == table)
    return [f for f in role["fields"] if f not in INPUT_ONLY]


def map_value(text: str, vocab: dict[str, list[str]]) -> str | None:
    have = set(tokens(text))
    for canon, synonyms in vocab.items():
        if any(set(tokens(s)) <= have for s in [canon.replace("_", " ")] + synonyms):
            return canon
    return None


def _header_score(header: str, synonyms: list[str]) -> int:
    have = tokens(header)
    best = 0
    for i, synonym in enumerate(synonyms):
        want = tokens(synonym)
        if want and want == have:
            best = max(best, 100 - i)
        elif want and set(want) <= set(have):
            best = max(best, 50 - i)
    return best


def match_fields(role: str, profile: dict) -> tuple[dict[str, str], list[str]]:
    """Field -> header for one file, greedy on header score; value fields fall back to value profiles."""
    spec, columns, notes = ROLES[role]["fields"], profile["columns"], []
    candidates = []
    for field, (kind, synonyms) in spec.items():
        for header, col in columns.items():
            if col["type"] != "empty" and col["type"] not in TYPES[kind]:
                continue
            score = _header_score(header, [field.replace("_", " ")] + synonyms)
            if score:
                candidates.append((score, field, header))
    candidates.sort(key=lambda c: -c[0])  # stable: equal scores keep field order, then column order
    chosen: dict[str, str] = {}
    for score, field, header in candidates:
        if field in chosen or header in chosen.values():
            continue
        rivals = [h for s, f, h in candidates if f == field and s == score and h != header and h not in chosen.values()]
        if rivals:
            notes.append(f"{field}: '{header}' and {rivals} score the same; took the first column")
        chosen[field] = header
    for field, (kind, _) in spec.items():
        vocab = VALUE_MAPS.get((role, field))
        if field in chosen or not vocab:
            continue
        best = max(((sum(map_value(v, vocab) is not None for v in col["values"]) / len(col["values"]), h)
                    for h, col in columns.items()
                    if h not in chosen.values() and col["type"] == "text" and col["values"]), default=(0, None))
        if best[0] >= 0.8:
            chosen[field] = best[1]
            notes.append(f"{field}: '{best[1]}' chosen by its values, not its header")
    return {f: chosen[f] for f in spec if f in chosen}, notes


def _complete(role: str, fields: dict) -> bool:
    spec = ROLES[role]
    return all(f in fields for f in spec["required"]) and (
        "any_of" not in spec or any(all(f in fields for f in group) for group in spec["any_of"]))


def map_upload(profiles: dict[str, dict]) -> dict:
    options = []
    for role, spec in ROLES.items():
        for name, profile in profiles.items():
            fields, notes = match_fields(role, profile)
            if not _complete(role, fields):
                continue
            score = sum(2 if f in spec["required"] else 1 for f in fields)
            stem = set(tokens(Path(name).stem))
            named = any(set(tokens(s)) <= stem for s in spec["files"])
            if not named and len(fields) == len(spec["required"]):
                continue  # a generic header like 'Code' alone is no reason to take an unrelated file
            score += 3 * named
            key = profile["columns"][fields[spec["key"]]]
            unique = key["distinct_ratio"] == 1 and key["null_rate"] == 0
            if spec.get("support") and not unique:
                continue  # a support table is only taken from a file it fits exactly
            score += 2 * unique
            options.append((score, role, name, fields, notes))
    options.sort(key=lambda o: -o[0])
    roles: dict[str, dict] = {}
    for score, role, name, fields, notes in options:
        if role in roles or any(r["file"] == name for r in roles.values()):
            continue
        columns = profiles[name]["columns"]
        entry = {"file": name, "score": score, "columns": fields, "date_formats": {}, "value_maps": {}, "notes": notes}
        for field, header in fields.items():
            kind = ROLES[role]["fields"][field][0]
            formats = columns[header]["date_formats"]
            if kind in ("date", "ts") and formats:
                entry["date_formats"][field] = formats[0]
                if len(formats) > 1:
                    notes.append(f"{field}: '{header}' fits {formats}; took {formats[0]} (day-first)")
            vocab = VALUE_MAPS.get((role, field))
            if vocab and columns[header]["values"]:
                entry["value_maps"][field] = {v: map_value(v, vocab) for v in columns[header]["values"]}
                unmapped = [v for v, c in entry["value_maps"][field].items() if c is None]
                if unmapped:
                    notes.append(f"{field}: values {unmapped} match no known meaning; kept as written")
        roles[role] = entry
    used = {r["file"] for r in roles.values()}
    return {
        "roles": {r: roles[r] for r in ROLES if r in roles},
        "missing_roles": {r: MISSING_REASON[r] for r in MISSING_REASON if r not in roles},
        "unused_files": [n for n in profiles if n not in used],
        "loss_types": LOSS_TYPES,
    }


def _convert(kind: str, raw: str, fmt: str | None, vmap: dict | None):
    raw = (raw or "").strip()
    if not raw:
        return None
    if kind in ("money", "int"):
        number = parse_number(raw)
        if kind == "int":
            if number != int(number):
                raise ValueError("not a whole number")
            return int(number)
        return number
    if kind in ("date", "ts"):
        if not fmt:
            raise ValueError("no date format")
        moment = parse_date(raw, fmt)
        return moment.date() if kind == "date" else moment
    if kind == "bool":
        if raw.lower() not in BOOLS:
            raise ValueError("not yes/no")
        return BOOLS[raw.lower()]
    if kind == "value":
        return (vmap or {}).get(raw) or raw.lower()
    return raw


def canonical(mapping: dict, upload: Path) -> tuple[dict[str, list[dict]], list[str]]:
    """Canonical tables as typed rows, plus every value that did not convert."""
    tables, errors = {}, []
    for role, spec in ROLES.items():
        entry = mapping["roles"].get(role)
        rows = []
        if entry:
            headers, source = read_csv(upload / entry["file"])
            bad: dict[str, list[str]] = {}
            errors += [f"{role}.{f}: column '{h}' is not in {entry['file']}"
                       for f, h in entry["columns"].items() if h not in headers]
            for src in source:
                row = {}
                for field, (kind, _) in spec["fields"].items():
                    header = entry["columns"].get(field)
                    raw = src.get(header, "") if header else ""
                    try:
                        row[field] = _convert(kind, raw, entry["date_formats"].get(field),
                                              entry["value_maps"].get(field))
                    except ValueError:
                        bad.setdefault(field, []).append(raw)
                        row[field] = None
                if role == "bank_txn" and "amount_ngn" not in entry["columns"]:
                    credit, debit = row["credit_ngn"], row["debit_ngn"]
                    row["direction"] = "credit" if credit else "debit" if debit else None
                    row["amount_ngn"] = abs(credit or debit) if (credit or debit) else None
                if role == "cost" and row["total_ngn"] is None and row["qty"] is not None and row["unit_cost_ngn"] is not None:
                    row["total_ngn"] = row["qty"] * row["unit_cost_ngn"]
                rows.append({c: row[c] for c in columns_of(spec["table"])})
            if role == "cost":  # one invoice often has a line per product: give each line its own id
                counts: dict = {}
                for r in rows:
                    counts[r["invoice_id"]] = counts.get(r["invoice_id"], 0) + 1
                seen: dict = {}
                for r in rows:
                    if r["invoice_id"] is not None and counts[r["invoice_id"]] > 1:
                        seen[r["invoice_id"]] = seen.get(r["invoice_id"], 0) + 1
                        r["invoice_id"] = f"{r['invoice_id']}-{seen[r['invoice_id']]}"
            for field, values in bad.items():
                errors.append(f"{role}.{field}: {len(values)} values in '{entry['columns'][field]}' "
                              f"do not read as {spec['fields'][field][0]} (e.g. {values[0]!r})")
        tables[spec["table"]] = rows
    if not tables["staff"]:  # derive from the sales, ids only
        ids = sorted({r["staff_id"] for r in tables["sales"] if r["staff_id"]})
        tables["staff"] = [{"staff_id": i, "name": i, "role": None} for i in ids]
    # The daily_pnl spine: every day from the first to the last sale day. A list of dates, not data.
    days = [r["sold_at"].date() for r in tables["sales"] if r["sold_at"]]
    first, last = (min(days), max(days)) if days else (None, None)
    tables["calendar"] = [{"cal_date": first + timedelta(d)} for d in range((last - first).days + 1)] if days else []
    return tables, errors


def cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, date) and hasattr(value, "hour"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)
