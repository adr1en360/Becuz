"""Live warehouse: the becuz USL in Zetaris over REST. Every statement passes the read-only guard first
and is recorded in the ledger. The admin setup scripts reuse ZetarisClient with the admin key."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

from becuz import ledger
from becuz.safety import is_read_only, read_http_error
from becuz.usl import USL

from . import QueryError


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


def _value(cell):
    # Zetaris returns every value as a string; numbers become floats so the critic can compare them.
    if isinstance(cell, str):
        try:
            return float(cell)
        except ValueError:
            return cell
    return cell


class ZetarisWarehouse:
    via = "zetaris"
    usl = USL

    def __init__(self, client: ZetarisClient, ledger_path=None):
        self.client, self.ledger_path = client, ledger_path

    @classmethod
    def from_config(cls, config) -> ZetarisWarehouse:
        return cls(ZetarisClient(config.zetaris_rest_url, config.zetaris_org_id, config.zetaris_api_key),
                   config.ledger_path)

    def query(self, sql: str) -> list[dict]:
        sql = sql.strip().rstrip(";").strip()
        if not is_read_only(sql):
            self._record(sql, error="refusing non-read-only SQL")
            raise QueryError("refusing non-read-only SQL")
        try:
            response = self.client.run_sql(sql)
        except ZetarisError as exc:
            self._record(sql, error=str(exc))
            # Network failures and timeouts come back as HTTP 0 and are worth retrying.
            raise QueryError(str(exc), transient=exc.status == 0) from exc
        found = rows(response)
        self._record(sql, count=len(found))
        headers = response.get("headers") or []
        return [dict(zip(headers, map(_value, row))) for row in found]

    def _record(self, sql: str, count: int = 0, error: str = "") -> None:
        entry = {"kind": "error", "ok": False, "error": error} if error else {"kind": "query", "ok": True, "row_count": count}
        ledger.write(self.ledger_path, {**entry, "tool": "query_data", "via": self.via, "sql": sql[:500]})
