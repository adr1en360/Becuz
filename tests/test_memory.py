from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from base.memory import JsonMemory, NullMemory


class MemoryTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            memory = JsonMemory(path)
            memory.remember("Customers churn when support is slow", {"source": "note"})
            memory.remember("Revenue grew in March")

            found = memory.recall("churn")
            self.assertEqual(len(found), 1)
            self.assertIn("churn", found[0].text.lower())
            self.assertEqual(found[0].metadata["source"], "note")

            again = JsonMemory(path)
            self.assertEqual(len(again.all()), 2)

    def test_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory = JsonMemory(Path(tmp) / "memory.json")
            memory.remember("one")
            memory.remember("two")
            memory.clear()
            self.assertEqual(memory.all(), [])

    def test_null(self) -> None:
        memory = NullMemory()
        memory.remember("x")
        self.assertEqual(memory.recall("x"), [])
        self.assertEqual(memory.all(), [])

    def test_corrupt_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            path.write_text("{bad", encoding="utf-8")
            memory = JsonMemory(path)
            self.assertEqual(memory.all(), [])
            backups = list(Path(tmp).glob("memory.json.corrupt-*"))
            self.assertEqual(len(backups), 1)
            self.assertFalse(path.exists())
            memory.remember("new")
            self.assertEqual([item.text for item in memory.all()], ["new"])

    def test_corrupt_item_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            path.write_text('[{"text": "keep"}, 42]', encoding="utf-8")
            memory = JsonMemory(path)
            self.assertEqual(memory.all(), [])
            backups = list(Path(tmp).glob("memory.json.corrupt-*"))
            self.assertEqual(len(backups), 1)
            self.assertFalse(path.exists())

    def test_recall_limit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memory = JsonMemory(Path(tmp) / "memory.json")
            memory.remember("one")
            memory.remember("two")
            self.assertEqual([item.text for item in memory.recall("", limit=0)], ["two"])


if __name__ == "__main__":
    unittest.main()
