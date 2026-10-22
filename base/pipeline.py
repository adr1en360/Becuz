from __future__ import annotations

from . import ledger, sample
from .config import Config
from .nightshift import NightshiftClient
from .nvidia import NvidiaClient
from .providers import AllProvidersFailed, Completion, ProviderError
from .tools import is_read_only, query_data
from .zetaris import rows as extract_rows


class Pipeline:
    def __init__(self, config: Config):
        self.config = config
        self.nightshift = NightshiftClient(
            config.nightshift_base_url, config.nightshift_token, config.nightshift_model
        )
        self.nvidia = NvidiaClient(config.nvidia_base_url, config.nvidia_api_key, config.nvidia_model)

    def ask(self, prompt: str, system: str = "", model: str | None = None) -> Completion:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.ask_messages(messages, label=prompt, model=model)

    def ask_messages(
        self, messages: list[dict], label: str = "", model: str | None = None
    ) -> Completion:
        """Single generator seam. Every engine should call this, not a provider."""
        if self.config.sample_mode:
            result = sample.completion(messages)
            self._record_model(result, label or _last_user(messages))
            return result

        errors: list[str] = []
        if self.config.has_nightshift:
            try:
                result = self.nightshift.complete(messages, model=model)
                if not result.text.strip():
                    raise ProviderError("nightshift", 0, "empty completion")
                self._record_model(result, label or _last_user(messages))
                return result
            except ProviderError as exc:
                errors.append(str(exc))
        if self.config.has_nvidia:
            try:
                result = self.nvidia.complete(messages, model=model)
                if not result.text.strip():
                    raise ProviderError("nvidia-direct", 0, "empty completion")
                self._record_model(result, label or _last_user(messages))
                return result
            except ProviderError as exc:
                errors.append(str(exc))
        self._record_error(label or _last_user(messages), errors)
        raise AllProvidersFailed(errors or ["no AI provider configured"])

    def query(self, sql: str) -> dict:
        sql = (sql or "").strip()
        while sql.endswith(";"):
            sql = sql[:-1].strip()
        if not is_read_only(sql):
            self._record_query_error(sql, "refusing non-read-only SQL")
            return {"ok": False, "tool": "query_data", "error": "refusing non-read-only SQL"}
        if self.config.sample_mode:
            rows = sample.rows(sql)
            response = {"headers": ["sample"], "data": rows, "total": len(rows)}
            self._record_query(sql, response, via="sample")
            return {
                "ok": True,
                "tool": "query_data",
                "sql": sql,
                "rows": rows,
                "raw": response,
                "sample": True,
            }
        try:
            response = query_data(sql, self.config)
        except Exception as exc:
            self._record_query_error(sql, str(exc))
            return {"ok": False, "tool": "query_data", "error": str(exc)}
        self._record_query(sql, response)
        return {
            "ok": True,
            "tool": "query_data",
            "sql": sql,
            "rows": extract_rows(response),
            "raw": response,
        }

    def answer(self, prompt: str, system: str = "") -> dict:
        try:
            completion = self.ask(prompt, system=system)
        except AllProvidersFailed as exc:
            return {"ok": False, "tool": "ask_model", "error": str(exc)}
        return {
            "ok": True,
            "tool": "ask_model",
            "via": completion.via,
            "model": completion.model,
            "signed": completion.signed,
            "answer": completion.text,
        }

    def blocked(self, request: str, reason: str) -> dict:
        self._record_blocked(request, reason)
        return {"ok": False, "blocked": True, "reason": reason}

    def _record_model(self, completion: Completion, prompt: str) -> None:
        ledger.write(
            self.config.ledger_path,
            {
                "kind": "model",
                "tool": "ask_model",
                "ok": True,
                "via": completion.via,
                "provider": completion.provider,
                "model": completion.model,
                "request_id": completion.request_id,
                "signed": completion.signed,
                "request": prompt[:200],
            },
        )

    def _record_query(self, sql: str, response: dict, via: str = "zetaris") -> None:
        ledger.write(
            self.config.ledger_path,
            {
                "kind": "query",
                "tool": "query_data",
                "ok": True,
                "via": via,
                "provider": via,
                "sql": sql[:500],
                "row_count": len(extract_rows(response)),
            },
        )

    def _record_blocked(self, request: str, reason: str) -> None:
        ledger.write(
            self.config.ledger_path,
            {
                "kind": "blocked",
                "tool": "blocked",
                "ok": False,
                "reason": reason,
                "request": request[:200],
            },
        )

    def _record_error(self, prompt: str, errors: list[str]) -> None:
        ledger.write(
            self.config.ledger_path,
            {
                "kind": "error",
                "tool": "ask_model",
                "ok": False,
                "error": " | ".join(errors),
                "request": prompt[:200],
            },
        )

    def _record_query_error(self, sql: str, error: str) -> None:
        ledger.write(
            self.config.ledger_path,
            {
                "kind": "error",
                "tool": "query_data",
                "ok": False,
                "error": error,
                "sql": sql[:500],
            },
        )


def _last_user(messages: list[dict]) -> str:
    for message in reversed(messages or []):
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return ""
