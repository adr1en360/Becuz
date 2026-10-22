from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

from .providers import read_http_error


class ZetarisError(RuntimeError):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"zetaris: HTTP {status}: {message}")


class ZetarisClient:
    def __init__(self, rest_url: str, org_id: str, api_key: str):
        self.rest_url = rest_url.rstrip("/")
        self.org_id = org_id
        self.api_key = api_key

    def run_sql(self, sql: str, limit: int = 100, timeout: int = 60) -> dict:
        if not (self.rest_url and self.org_id and self.api_key):
            raise ZetarisError(0, "missing ZETARIS_REST_URL, ZETARIS_ORG_ID, or ZETARIS_API_KEY")
        payload = {
            "queryId": str(uuid.uuid4()),
            "sql": sql,
            "source": "SqlEditor",
            "limit": limit,
        }
        request = urllib.request.Request(
            f"{self.rest_url}/sql-editor/sqls/run",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "X-Org-ID": self.org_id,
                "X-Request-ID": str(uuid.uuid4()),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ZetarisError(exc.code, read_http_error(exc)) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise ZetarisError(0, str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise ZetarisError(0, "invalid JSON response") from exc


def rows(response) -> list:
    if isinstance(response, list):
        return response
    if not isinstance(response, dict):
        return []
    for key in ("rows", "data", "result", "results"):
        value = response.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            found = rows(value)
            if found:
                return found
    return []
