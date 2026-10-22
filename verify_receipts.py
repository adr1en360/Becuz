from __future__ import annotations

import json
from pathlib import Path

from base import ledger
from base.config import load
from base.nightshift import find_receipt


def verify(ledger_path: Path, receipt_path: Path | None = None) -> int:
    """Append one model_receipt event for each settled Nightshift receipt."""
    if not ledger_path.exists():
        return 0
    entries = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)

    verified = {
        entry.get("request_id")
        for entry in entries
        if entry.get("kind") == "model_receipt" and entry.get("request_id")
    }
    pending = [
        entry
        for entry in entries
        if entry.get("kind") == "model"
        and entry.get("via") == "nightshift"
        and entry.get("request_id")
        and entry.get("request_id") not in verified
    ]

    count = 0
    for entry in pending:
        request_id = str(entry["request_id"])
        if request_id in verified:
            continue
        receipt = find_receipt(request_id, receipt_path, tries=1)
        if not receipt.get("_proof"):
            continue
        if ledger.write(
            ledger_path,
            {
                "kind": "model_receipt",
                "tool": "ask_model",
                "ok": True,
                "via": "nightshift",
                "request_id": request_id,
                "receipt_id": receipt.get("receipt_id", ""),
                "signed": True,
                "request": str(entry.get("request", ""))[:200],
            },
        ):
            count += 1
            verified.add(request_id)
    return count


def main() -> int:
    config = load()
    if config.ledger_path is None:
        print("ledger disabled (LEDGER_PATH=none)")
        return 0
    count = verify(config.ledger_path)
    print(f"verified {count} receipt(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
