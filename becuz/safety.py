"""Safety checks every query and log line passes: the read-only SQL guard and secret redaction."""
from __future__ import annotations

import re
import urllib.error

ALLOWED_START = re.compile(r"^(select|with|show|describe|desc|explain)\b", re.IGNORECASE)
DML = re.compile(
    r"\b(insert|update|delete|merge|drop|alter|create|truncate|grant|revoke|call|exec|execute|copy|vacuum|attach|detach|pragma|set|begin|commit|rollback|upsert)\b",
    re.IGNORECASE,
)
SHOW_CREATE = re.compile(
    r"^show\s+create\s+(?:table|view|database|index)\b", re.IGNORECASE
)
# Spark functions that call arbitrary Java or have side effects inside a SELECT.
SIDE_EFFECT = re.compile(r"\b(reflect|java_method|assert_true|raise_error)\s*\(", re.IGNORECASE)
# Hive script transform: SELECT TRANSFORM(...) USING 'command' runs a process.
# strip_literals has already blanked the command to '' (JOIN ... USING (col) is unaffected).
SCRIPT = re.compile(r"\busing\s*(''|\"\"|``)", re.IGNORECASE)
# Marks a literal the scanner cannot read safely; is_read_only rejects text containing it.
UNSAFE = "\x00"


def strip_literals(sql: str) -> str:
    """Blank strings and comments in one pass; context decides what they are."""
    out: list[str] = []
    i = 0
    size = len(sql)
    while i < size:
        char = sql[i]
        nxt = sql[i + 1] if i + 1 < size else ""
        if char in ("'", '"', "`"):
            out.append(char * 2)
            i += 1
            closed = False
            while i < size:
                if sql[i] == "\\":
                    # Only string literals take backslash escapes; elsewhere the engine
                    # may end the token here, so fail closed.
                    if char != "'":
                        out.append(UNSAFE)
                    i += 2
                    continue
                if sql[i] == char:
                    if i + 1 < size and sql[i + 1] == char:
                        i += 2
                        continue
                    i += 1
                    closed = True
                    break
                i += 1
            if not closed:
                out.append(UNSAFE)
        elif char == "-" and nxt == "-":
            out.append(" ")
            i += 2
            while i < size and sql[i] not in "\r\n":
                i += 1
        elif char == "/" and nxt == "*":
            out.append(" ")
            i += 2
            while i < size:
                if sql[i] == "*" and i + 1 < size and sql[i + 1] == "/":
                    i += 2
                    break
                i += 1
        else:
            out.append(char)
            i += 1
    return "".join(out)


def is_read_only(sql: str) -> bool:
    text = sql.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    if not text:
        return False
    probe = strip_literals(text).strip()
    if not probe or UNSAFE in probe:
        return False
    if ";" in probe.rstrip(";"):
        return False
    probe = probe.rstrip(";").strip()
    if not ALLOWED_START.match(probe):
        return False
    if re.search(r"\binto\b", probe, re.IGNORECASE):
        return False
    scan = SHOW_CREATE.sub("show ", probe, count=1) if SHOW_CREATE.match(probe) else probe
    if DML.search(scan) or SIDE_EFFECT.search(scan) or SCRIPT.search(scan):
        return False
    if re.match(r"^explain\b", probe, re.IGNORECASE) and not re.match(
        r"^explain\s+(select|with|analyze)\b", probe, re.IGNORECASE
    ):
        return False
    return True



_SECRET = re.compile(r"nvapi-[A-Za-z0-9_-]+")
_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+")


def redact(text: str) -> str:
    text = _SECRET.sub("nvapi-REDACTED", text)
    return _BEARER.sub("Bearer REDACTED", text)


def read_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = str(exc.reason or "request failed")
    return redact(body[:800])
