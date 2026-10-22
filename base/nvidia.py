from __future__ import annotations

import json
import urllib.error
import urllib.request

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


class NvidiaClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(self, messages: list[dict], model: str | None = None, timeout: int = 120) -> Completion:
        if not self.api_key:
            raise RuntimeUnavailable("nvidia-direct", "no NVIDIA_API_KEY")
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = read_http_error(exc)
            if exc.code in (404, 410) or looks_retired(detail):
                raise ModelRetired("nvidia-direct", exc.code, detail) from exc
            raise ProviderError("nvidia-direct", exc.code, detail) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise RuntimeUnavailable("nvidia-direct", str(exc)) from exc
        except UnicodeDecodeError as exc:
            raise ProviderError("nvidia-direct", 0, "invalid UTF-8 response") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("nvidia-direct", 0, "invalid JSON response") from exc

        message = first_message(body, "nvidia-direct")
        text = message_text(message, "nvidia-direct")
        if not text.strip():
            raise ProviderError("nvidia-direct", 0, "empty answer")
        return Completion(
            text=clean_answer(text),
            provider="nvidia-direct",
            model=body.get("model") or (model or self.model),
            via="nvidia-direct",
            request_id=str(body.get("id") or ""),
        )
