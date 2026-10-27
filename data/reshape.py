"""Turn a scenario into a differently shaped upload, as a real shop's exports might look.

Same records, other file names, headers, column order, date formats and value words; no stock file.
Reads the source by header name, so it follows whatever the generator writes.

    uv run python -m data.reshape            # data/scenarios/s01 -> data/uploads/s06
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYMENT = {"cash": "Cash", "pos_card": "POS", "transfer": "Bank Transfer"}
CHANNEL = {"transfer": "NIP Transfer", "pos_settlement": "POS Settlement", "cash_deposit": "Cash Deposit",
           "charge": "Bank Charges"}


def _rows(src: Path, name: str) -> list[dict]:
    with (src / f"{name}.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _day(text: str, fmt: str) -> str:
    return datetime.fromisoformat(text).strftime(fmt) if text else ""


def _money(text: str) -> str:
    return f"{float(text):,.2f}" if text else ""


def reshape(src: Path, dst: Path) -> None:
    files = {
        "sales_export.csv": [{
            "Date/Time": _day(r["sold_at"], "%d/%m/%Y %H:%M"), "Txn Ref": r["sale_id"], "Cashier": r["staff_id"],
            "Paid Via": PAYMENT.get(r["payment_method"], r["payment_method"]), "Transfer No": r["transfer_ref"],
            "Gross": _money(r["gross_ngn"]), "Disc": _money(r["discount_ngn"]), "Amount (NGN)": _money(r["net_ngn"]),
        } for r in _rows(src, "sales")],
        "items_sold.csv": [{
            "Item Row": r["line_id"], "Txn Ref": r["sale_id"], "Item Code": r["product_id"], "Quantity": r["qty"],
            "Price": r["unit_price_ngn"], "Item Discount": r["discount_ngn"], "Promo Code": r["promo_id"],
        } for r in _rows(src, "sale_lines")],
        "items.csv": [{
            "Item Code": r["product_id"], "SKU": r["sku"], "Description": r["name"], "Group": r["category"],
            "Unit": r["unit"], "Price": r["list_price_ngn"], "Perishable": "Yes" if r["is_perishable"] == "true" else "No",
        } for r in _rows(src, "products")],
        "purchases.csv": [{
            "Invoice No": r["invoice_id"], "Invoice Date": _day(r["invoice_date"], "%d/%m/%Y"),
            "Supplier Code": r["supplier_id"], "Supplier": r["supplier_name"], "Item Code": r["product_id"],
            "Quantity": r["qty"], "Cost Price": r["unit_cost_ngn"], "Line Total": r["total_ngn"],
        } for r in _rows(src, "supplier_invoices")],
        "spending.csv": [{
            "Ref": r["expense_id"], "Paid On": _day(r["expense_date"], "%d-%b-%Y"), "Type": r["category"],
            "Amount Paid": r["amount_ngn"], "Period Start": _day(r.get("cover_start", ""), "%d/%m/%Y"),
            "Period End": _day(r.get("cover_end", ""), "%d/%m/%Y"), "Memo": r["note"],
        } for r in _rows(src, "expenses")],
        "bank.csv": [{
            "Tran ID": r["txn_id"], "Txn Date": _day(r["posted_at"], "%d/%m/%Y %H:%M"), "Description": r["narration"],
            "Reference": r["ref"], "Debit": r["amount_ngn"] if r["direction"] == "debit" else "",
            "Credit": r["amount_ngn"] if r["direction"] == "credit" else "",
            "Channel": CHANNEL.get(r["channel"], r["channel"]), "Counterparty": r["counterparty"],
        } for r in _rows(src, "bank_statement")],
        "discounts.csv": [{
            "Promo Code": r["promo_id"], "Item Code": r["product_id"], "Percent Off": r["pct_off"],
            "Starts": _day(r["start_date"], "%d/%m/%Y"), "Ends": _day(r["end_date"], "%d/%m/%Y"),
        } for r in _rows(src, "promos")],
        "team.csv": [{"Staff Code": r["staff_id"], "Full Name": r["name"], "Position": r["role"]}
                     for r in _rows(src, "staff")],
        "rates.csv": [{"Day": _day(r["date"], "%d/%m/%Y"), "USD Rate": r["usd_ngn"]} for r in _rows(src, "fx_rates")],
    }
    dst.mkdir(parents=True, exist_ok=True)
    for name, rows in files.items():
        with (dst / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    src, dst = (Path(a) for a in sys.argv[1:3]) if len(sys.argv) == 3 else (HERE / "scenarios" / "s01", HERE / "uploads" / "s06")
    reshape(src, dst)
    print(f"wrote {dst}")
