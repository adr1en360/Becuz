"""Meterless Nightshift, the only model provider. Every model call goes through Nightshift.ask_messages,
which records each call (or its failure) in the ledger and attaches the signed receipt when one exists."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from becuz import ledger
from becuz.safety import read_http_error


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


def clean_answer(text: str) -> str:
    for marker in ("</think>", "<｜end▁of▁thinking｜>"):
        if marker in text:
            text = text.split(marker, 1)[1]
    return text.strip()


def first_message(body: object) -> dict:
    if not isinstance(body, dict):
        raise ProviderError("nightshift", 0, "invalid response body")
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ProviderError("nightshift", 0, "empty choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ProviderError("nightshift", 0, "invalid message")
    return message


def message_text(message: dict) -> str:
    content = message.get("content") or ""
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if not isinstance(part, dict) or not isinstance(part.get("text"), str):
                raise ProviderError("nightshift", 0, "invalid content part")
            parts.append(part["text"])
        content = "".join(parts)
    if not isinstance(content, str):
        raise ProviderError("nightshift", 0, "invalid content")
    return content


class Nightshift:
    via = "nightshift"

    def __init__(self, config):
        self.base_url = config.nightshift_base_url.rstrip("/")
        self.token = config.nightshift_token
        self.model = config.nightshift_model
        self.ledger_path = config.ledger_path

    def ask_messages(self, messages: list[dict], label: str = "", model: str | None = None) -> Completion:
        label = label or _last_user(messages)
        try:
            result = self.complete(messages, model=model)
        except ProviderError as exc:
            ledger.write(self.ledger_path, {"kind": "error", "tool": "ask_model", "ok": False,
                                            "error": str(exc), "request": label[:200]})
            raise
        ledger.write(self.ledger_path, {"kind": "model", "tool": "ask_model", "ok": True, "via": result.via,
                                        "model": result.model, "request_id": result.request_id,
                                        "signed": result.signed, "request": label[:200]})
        return result

    def complete(self, messages: list[dict], model: str | None = None, timeout: int = 120) -> Completion:
        if not self.token:
            raise ProviderError("nightshift", 0, "no runtime token")
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4096,  # thinking models (Nemotron 3.5 Lightning) reason before answering; 1024 left the answer empty
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
                "meterless-app": "becuz",
                "meterless-scope": "user",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ProviderError("nightshift", exc.code, read_http_error(exc)) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise ProviderError("nightshift", 0, str(exc)) from exc
        except UnicodeDecodeError as exc:
            raise ProviderError("nightshift", 0, "invalid UTF-8 response") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("nightshift", 0, "invalid JSON response") from exc

        text = clean_answer(message_text(first_message(body)))
        if not text:
            raise ProviderError("nightshift", 0, "empty answer")
        request_id = str(body.get("id") or "")
        receipt = find_receipt(request_id)
        return Completion(
            text=text,
            model=body.get("model") or (model or self.model),
            via="nightshift",
            request_id=request_id,
            signed=bool(receipt.get("_proof")),
            receipt=receipt,
        )


def find_receipt(
    request_id: str,
    path: Path | None = None,
    tries: int = 3,
    delay: float = 0.15,
) -> dict:
    if not request_id:
        return {}
    if path is None:
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            return {}
        path = Path(appdata) / "ai.meterless.runtime" / "meterless.json"
    fallback: dict = {}
    for attempt in range(max(1, tries)):
        data = None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
        if isinstance(data, dict):
            receipts = data.get("receipts")
            if isinstance(receipts, list):
                for receipt in receipts:
                    if not isinstance(receipt, dict) or receipt.get("request_id") != request_id:
                        continue
                    if receipt.get("_proof"):
                        return receipt
                    fallback = fallback or receipt
        if attempt + 1 < tries and delay > 0:
            time.sleep(delay)
    return fallback


def _last_user(messages: list[dict]) -> str:
    for message in reversed(messages or []):
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return ""
