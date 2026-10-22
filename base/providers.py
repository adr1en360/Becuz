from __future__ import annotations

import re
import urllib.error
from dataclasses import dataclass, field


@dataclass
class Completion:
    text: str
    model: str
    via: str
    request_id: str = ""
    signed: bool = False
    receipt: dict = field(default_factory=dict)


class ProviderError(RuntimeError):
    def __init__(self, provider: str, status: int, message: str):
        self.provider = provider
        self.status = status
        self.message = message
        super().__init__(f"{provider}: HTTP {status}: {message}")


_SECRET = re.compile(r"nvapi-[A-Za-z0-9_-]+")
_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+")


def redact(text: str) -> str:
    text = _SECRET.sub("nvapi-REDACTED", text)
    return _BEARER.sub("Bearer REDACTED", text)


def clean_answer(text: str) -> str:
    for marker in ("</think>", "<｜end▁of▁thinking｜>"):
        if marker in text:
            text = text.split(marker, 1)[1]
    return text.strip()


def first_message(body: object, provider: str) -> dict:
    if not isinstance(body, dict):
        raise ProviderError(provider, 0, "invalid response body")
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ProviderError(provider, 0, "empty choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ProviderError(provider, 0, "invalid message")
    return message


def message_text(message: dict, provider: str) -> str:
    content = message.get("content") or ""
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if not isinstance(part, dict) or not isinstance(part.get("text"), str):
                raise ProviderError(provider, 0, "invalid content part")
            parts.append(part["text"])
        content = "".join(parts)
    if not isinstance(content, str):
        raise ProviderError(provider, 0, "invalid content")
    return content


def read_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = str(exc.reason or "request failed")
    return redact(body[:800])

