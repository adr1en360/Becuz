"""Owner-facing wording shared by the agents: naira amounts and plurals, said the same way everywhere."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def naira(value: float) -> str:
    # Round halves up (6,562.50 -> 6,563), as the web UI does, so the same figure never shows two ways.
    return f"₦{Decimal(str(abs(value))).quantize(Decimal(1), ROUND_HALF_UP):,}"


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' * (n != 1)}"


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]
