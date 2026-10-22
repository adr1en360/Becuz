from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .providers import redact


def write(path: Path, entry: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **entry,
        }
        line = redact(json.dumps(record, ensure_ascii=True))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return True
    except (OSError, TypeError, ValueError) as exc:
        # Evidence is best effort; a failed write must not break the answer.
        print(f"ledger: {exc}", file=sys.stderr)
        return False
