from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Values that switch a log path off.
OFF = {"none", "null", "off", "false"}


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _runtime_token() -> str:
    token = os.getenv("METERLESS_RUNTIME_TOKEN", "").strip()
    if token:
        return token
    local = os.environ.get("LOCALAPPDATA", "")
    if not local:
        return ""
    path = Path(local) / "ai.meterless.runtime" / "proxy-token"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def _path(name: str, default: Path) -> Path | None:
    raw = os.getenv(name, "").strip()
    if raw.lower() in OFF:
        return None
    path = Path(raw).expanduser() if raw else default
    return path if path.is_absolute() else ROOT / path


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        # A typo in .env must not stop a judge from starting the app.
        print(f"config: {name}={raw!r} is not a number; using {default}", file=sys.stderr)
        return default


def _value(name: str) -> str:
    """A setting from the environment; an unfilled .env.example placeholder like <org-id> counts as missing."""
    raw = os.getenv(name, "").strip()
    return "" if raw.startswith("<") else raw


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    zetaris_rest_url: str
    zetaris_org_id: str
    zetaris_api_key: str
    nightshift_base_url: str
    nightshift_token: str
    nightshift_model: str
    ledger_path: Path | None
    trace_path: Path | None
    sample_mode: bool
    server_host: str
    server_port: int

    @property
    def has_zetaris(self) -> bool:
        return bool(self.zetaris_rest_url and self.zetaris_org_id and self.zetaris_api_key)

    @property
    def has_nightshift(self) -> bool:
        return bool(self.nightshift_token)


def load() -> Config:
    _load_env(ROOT / ".env")
    return Config(
        zetaris_rest_url=_value("ZETARIS_REST_URL").rstrip("/"),
        zetaris_org_id=_value("ZETARIS_ORG_ID"),
        zetaris_api_key=_value("ZETARIS_API_KEY"),
        nightshift_base_url=os.getenv("METERLESS_BASE_URL", "http://127.0.0.1:8088/v1").rstrip("/"),
        nightshift_token=_runtime_token(),
        nightshift_model=os.getenv("METERLESS_MODEL", "meterless/auto").strip(),
        ledger_path=_path("LEDGER_PATH", ROOT / "logs" / "ledger.jsonl"),
        trace_path=_path("TRACE_PATH", ROOT / "logs" / "trace.jsonl"),
        sample_mode=_flag("SAMPLE_MODE"),
        server_host=os.getenv("SERVER_HOST", "127.0.0.1").strip(),
        server_port=_int("SERVER_PORT", 8000),
    )
