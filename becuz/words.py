"""Owner-facing wording shared by the agents: naira amounts and plurals, said the same way everywhere."""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal


def naira(value: float) -> str:
    # Round halves up (6,562.50 -> 6,563), as the web UI does, so the same figure never shows two ways.
    return f"₦{Decimal(str(abs(value))).quantize(Decimal(1), ROUND_HALF_UP):,}"


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' * (n != 1)}"


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def span(start: date, end: date) -> tuple[str, str]:
    """The period as the owner reads it: ("these 3 days", "in these 3 days"), or ("this day", "on this day")."""
    days = (end - start).days + 1
    return ("this day", "on this day") if days == 1 else (f"these {days} days", f"in these {days} days")


def baseline_words(start: date, end: date) -> str:
    days = (end - start).days + 1
    if days == 1:
        return "the average of the same weekday in the 4 weeks before"
    if days < 7:
        return f"the average of the same {days} days of the week in the 4 weeks before"
    if days == 7:
        return "the average of the 4 weeks before"
    return f"the average of 4 earlier periods of {days} days, starting on the same weekday"
