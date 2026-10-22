from __future__ import annotations

import json
import re
import sys
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

WORD = re.compile(r"[a-z0-9]{3,}")


@dataclass
class MemoryItem:
    text: str
    metadata: dict = field(default_factory=dict)
    namespace: str = "default"
    ts: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryItem":
        return cls(
            text=str(data.get("text", "")),
            metadata=data.get("metadata") or {},
            namespace=str(data.get("namespace", "default")),
            ts=str(data.get("ts", "")),
        )


class Memory(Protocol):
    def remember(
        self, text: str, metadata: dict | None = None, namespace: str = "default"
    ) -> None: ...

    def recall(
        self, query: str, limit: int = 5, namespace: str = "default"
    ) -> list[MemoryItem]: ...

    def all(self, namespace: str | None = None) -> list[MemoryItem]: ...

    def clear(self, namespace: str | None = None) -> None: ...


class NullMemory:
    def remember(
        self, text: str, metadata: dict | None = None, namespace: str = "default"
    ) -> None:
        return None

    def recall(
        self, query: str, limit: int = 5, namespace: str = "default"
    ) -> list[MemoryItem]:
        return []

    def all(self, namespace: str | None = None) -> list[MemoryItem]:
        return []

    def clear(self, namespace: str | None = None) -> None:
        return None


def _tokens(text: str) -> set[str]:
    return set(WORD.findall((text or "").lower()))


class JsonMemory:
    """Small local stand-in for the H-MEM slot."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _load(self) -> list[MemoryItem]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._backup_corrupt()
            return []
        except OSError as exc:
            print(f"memory: {exc}", file=sys.stderr)
            return []
        if not isinstance(data, list):
            self._backup_corrupt()
            return []
        if not all(isinstance(item, dict) for item in data):
            self._backup_corrupt()
            return []
        return [MemoryItem.from_dict(item) for item in data]

    def _backup_corrupt(self) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = self.path.with_name(f"{self.path.name}.corrupt-{stamp}")
        try:
            self.path.replace(backup)
        except OSError as exc:
            print(f"memory: {exc}", file=sys.stderr)
            return
        print(f"memory: corrupt file moved to {backup.name}", file=sys.stderr)

    def _save(self, items: list[MemoryItem]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(self.path.name + ".tmp")
        payload = [asdict(item) for item in items]
        temp.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def remember(
        self, text: str, metadata: dict | None = None, namespace: str = "default"
    ) -> None:
        text = (text or "").strip()
        if not text:
            return
        item = MemoryItem(text=text[:4000], metadata=metadata or {}, namespace=namespace)
        with self._lock:
            items = self._load()
            items.append(item)
            self._save(items)

    def recall(
        self, query: str, limit: int = 5, namespace: str = "default"
    ) -> list[MemoryItem]:
        limit = max(1, int(limit))
        terms = _tokens(query)
        with self._lock:
            items = [item for item in self._load() if item.namespace == namespace]
        if not terms:
            return list(reversed(items[-limit:]))
        scored = []
        for item in items:
            score = len(terms & _tokens(item.text))
            if score:
                scored.append((score, item.ts, item))
        scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
        return [row[2] for row in scored[:limit]]

    def all(self, namespace: str | None = None) -> list[MemoryItem]:
        with self._lock:
            items = self._load()
        if namespace is None:
            return items
        return [item for item in items if item.namespace == namespace]

    def clear(self, namespace: str | None = None) -> None:
        with self._lock:
            if namespace is None:
                self._save([])
                return
            self._save([item for item in self._load() if item.namespace != namespace])
