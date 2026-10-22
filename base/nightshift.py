from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from .providers import (
    Completion,
    ModelRetired,
    ProviderError,
    RuntimeUnavailable,
    clean_answer,
    first_message,
    looks_retired,
    message_text,
    read_http_error,
)


class NightshiftClient:
    def __init__(self, base_url: str, token: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.model = model

    def complete(self, messages: list[dict], model: str | None = None, timeout: int = 120) -> Completion:
        if not self.token:
            raise RuntimeUnavailable("nightshift", "no runtime token")
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
                "meterless-app": "open-agent",
                "meterless-scope": "user",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = read_http_error(exc)
            if exc.code == 410 or looks_retired(detail):
                raise ModelRetired("nightshift", exc.code, detail) from exc
            raise ProviderError("nightshift", exc.code, detail) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise RuntimeUnavailable("nightshift", str(exc)) from exc
        except UnicodeDecodeError as exc:
            raise ProviderError("nightshift", 0, "invalid UTF-8 response") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("nightshift", 0, "invalid JSON response") from exc

        message = first_message(body, "nightshift")
        text = message_text(message, "nightshift")
        if not text.strip():
            raise ProviderError("nightshift", 0, "empty answer")
        request_id = str(body.get("id") or "")
        receipt = find_receipt(request_id)
        return Completion(
            text=clean_answer(text),
            provider="nightshift",
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
