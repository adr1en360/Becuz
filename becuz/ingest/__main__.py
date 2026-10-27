"""uv run python -m becuz.ingest <upload_dir> <out_dir> [--mapping reviewed.json]

Writes mapping.json and, when every check passes, the canonical CSVs. Exits 1 if a check fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import ingest


def report(mapping: dict) -> str:
    lines = ["Mapped:"]
    for role, entry in mapping["roles"].items():
        cols = ", ".join(f"{h} -> {f}" for f, h in entry["columns"].items())
        lines.append(f"  {role:<15} from {entry['file']}: {cols}")
        for field, values in entry["value_maps"].items():
            pairs = ", ".join(f"{v} -> {c or '(unknown)'}" for v, c in values.items())
            lines.append(f"  {'':<15} {field} values: {pairs}")
        lines += [f"  {'':<15} note: {n}" for n in entry["notes"]]
    for role, reason in mapping["missing_roles"].items():
        lines.append(f"Missing: {role} (causes that need it are not tested: {reason})")
    if mapping["unused_files"]:
        lines.append(f"Unused files: {', '.join(mapping['unused_files'])}")
    lines.append("Checks:")
    lines += [f"  {'PASS' if c['ok'] else 'FAIL'} {c['check']}: {c['detail']}" for c in mapping["checks"]]
    lines.append("Result: " + ("PASS, canonical files written" if mapping["ok"] else "FAIL, mapping blocked; nothing written but mapping.json"))
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # headers and values may hold ₦
    if len(argv) not in (2, 4) or (len(argv) == 4 and argv[2] != "--mapping"):
        print(__doc__)
        return 2
    reviewed = json.loads(Path(argv[3]).read_text(encoding="utf-8")) if len(argv) == 4 else None
    mapping = ingest(Path(argv[0]), Path(argv[1]), reviewed)
    print(report(mapping))
    return 0 if mapping["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
