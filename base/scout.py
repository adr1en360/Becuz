from __future__ import annotations

import re
from dataclasses import dataclass

from .tools import is_read_only, strip_literals

SQL_START = re.compile(
    r"^(?:select\s+(?:distinct\s+|all\s+)?(?:"
    r"\*|\(|\[|[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?=\s*(?:,|from\b|as\b|is\b|in\b|like\b|not\b|and\b|or\b|between\b|where\b|group\b|order\b|having\b|limit\b|union\b|except\b|intersect\b|[+\-*/%<>=|:!~)]|$))|'|\"|`|case\b|"
    r"(?:null|true|false|current_date|current_timestamp|current_user|session_user|current_schema|current_catalog|current_role|date|time|timestamp|interval|array|top\s+\d+)\b|"
    r"[\w.\"`]+\s*(?:,|from\b|\(|\[|as\b|is\b|in\b|like\b|not\b|and\b|or\b|between\b|[+\-*/%<>=|:!~])"
    r")|with\s+(?:recursive\s+)?[\w.\"`]+\s*(?:\([^)]*\)\s*)?as\s*\(\s*(?:select|with|values)\b)",
    re.IGNORECASE,
)
BARE_SELECT = re.compile(r"^SELECT\s+[\w.\"`]+\s*$")
SHOW_START = re.compile(
    r"^show\s+(?:(?:lightning\s+)?(?:tables|schemas|databases|namespaces|columns|views|functions|datasources|engines|grants)|create\s+(?:table|view|database|index))\b",
    re.IGNORECASE,
)
DESCRIBE_START = re.compile(
    r"^(?:describe|desc)\s+(?:table\s+)?[\w.\"`]+\s*$", re.IGNORECASE
)
EXPLAIN_PREFIX = re.compile(r"^explain\s+(?:analyze\s+)?", re.IGNORECASE)
QUESTION_START = re.compile(
    r"^(?:how|why|what|when|where|who|which|explain|describe|tell\s+me)\b",
    re.IGNORECASE,
)
HOW_TO_QUESTION = re.compile(
    r"^(?:(?:can|could|would|will|should|do|does|did)\s+"
    r"(?:you|i|we|someone|somebody)|show\s+me)\b.*\bhow\s+to\b",
    re.IGNORECASE,
)

DESTRUCTIVE = re.compile(
    r"\b(delete|drop|truncate|update|insert|alter|create|replace|merge|grant|revoke|vacuum|attach|detach|upsert)\b",
    re.IGNORECASE,
)
DML_PHRASE = re.compile(
    r"\b(?:"
    r"delete\s+(?:all\s+)?(?:rows?\s+)?from\s+[\w.\"`]+|"
    r"insert\s+into\s+(?!the\b|a\b|an\b|this\b|that\b)[\w.\"`]+|"
    r"update\s+(?!the\b|a\b|an\b|this\b|that\b)[\w.\"`]+\s+set|"
    r"(?:create|alter|drop)\s+(?:table|view|database|schema|index|function|procedure|role|user)|"
    r"truncate\s+(?:table\s+)?(?!the\b|a\b|an\b|this\b|that\b|it\b)[\w.\"`]+|"
    r"merge\s+into\s+[\w.\"`]+|replace\s+into\s+[\w.\"`]+|"
    r"grant\s+(?:select|insert|update|delete|all|usage|connect|execute|create|drop|alter|references|trigger|temporary)\b|"
    r"revoke\s+(?:select|insert|update|delete|all|usage|connect|execute|create|drop|alter|references|trigger|temporary)\b|"
    r"vacuum\s+(?!the\b|a\b|an\b|this\b|that\b)[\w.\"`]+|"
    r"attach\s+(?:database|table)\s+[\w.\"`]+|detach\s+(?:database|table)\s+[\w.\"`]+|"
    r"upsert\s+into\s+[\w.\"`]+|"
    r"call\s+[\w.\"`]+\s*\(|"
    r"exec(?:ute)?\s+(?!the\b|a\b|an\b|this\b|that\b|it\b|me\b|plan\b)[\w.\"`]+|"
    r"pragma\s+[\w.\"`]+|copy\s+[\w.\"`]+\s+(?:from|to)\s+(?:stdin|stdout|'')|"
    r"begin\s+(?:transaction|work)\b|commit\s*(?:work|transaction)?\s*$|"
    r"rollback\s*(?:work|transaction)?\s*$|"
    r"set\s+(?:session|transaction|role|search_path|timezone)\b|"
    r"set\s+[\w.\"`]+\s*="
    r")",
    re.IGNORECASE,
)
DATA_NOUN = re.compile(
    r"\b(rows?|records?|tables?|databases?|data|columns?|schema|view|index|users?|orders?|customers?)\b",
    re.IGNORECASE,
)


@dataclass
class Decision:
    tool: str
    reason: str
    sql: str = ""
    prompt: str = ""


def _clean(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    return text.rstrip(";").strip()


def _looks_like_sql(text: str) -> bool:
    probe = strip_literals(text).strip()
    explain = EXPLAIN_PREFIX.match(probe)
    if explain:
        rest = probe[explain.end():].lstrip()
        return bool(
            SQL_START.match(rest)
            or DML_PHRASE.search(probe)
            or DESTRUCTIVE.search(probe)
        )
    return bool(
        SQL_START.match(probe)
        or BARE_SELECT.match(probe)
        or SHOW_START.match(probe)
        or DESCRIBE_START.match(probe)
    )


def _destructive(text: str) -> bool:
    probe = strip_literals(text)
    if DML_PHRASE.search(probe):
        return True
    if not DESTRUCTIVE.search(probe):
        return False
    for match in DESTRUCTIVE.finditer(probe):
        tail = probe[match.end(): match.end() + 60]
        if DATA_NOUN.search(tail):
            return True
    return False


def classify(text: str) -> Decision:
    cleaned = _clean(text)
    if not cleaned:
        return Decision("blocked", "empty request")
    if HOW_TO_QUESTION.match(cleaned):
        return Decision("ask_model", "how-to question", prompt=cleaned)
    # A question only reaches the model, never the database, so block only SQL-shaped writes.
    if cleaned.endswith("?") and not DML_PHRASE.search(strip_literals(cleaned)):
        return Decision("ask_model", "question", prompt=cleaned)
    if QUESTION_START.match(cleaned) and not _looks_like_sql(cleaned):
        return Decision("ask_model", "question", prompt=cleaned)
    if _looks_like_sql(cleaned):
        if is_read_only(cleaned):
            return Decision("query_data", "read-only SQL", sql=cleaned)
        return Decision("blocked", "not a read-only query")
    if _destructive(cleaned):
        return Decision("blocked", "write or destructive request")
    return Decision("ask_model", "question", prompt=cleaned)
