from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from becuz.config import load
from becuz.investigate import BadRequest, investigate
from becuz.safety import redact

MAX_BODY = 1_000_000


class Handler(BaseHTTPRequestHandler):
    server_version = "Becuz/0.1"

    def do_GET(self) -> None:
        if self.path == "/health":
            config = self.server.config
            self._json(200, {"ok": True, "sample": config.sample_mode,
                             "providers": {"zetaris": config.has_zetaris, "nightshift": config.has_nightshift}})
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_OPTIONS(self) -> None:
        self._send(204, b"", "text/plain")  # CORS preflight for the web UI

    def do_POST(self) -> None:
        if self.path != "/run":
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._json(400, {"ok": False, "error": "invalid content length"})
            return
        if length < 0 or length > MAX_BODY:
            status = 400 if length < 0 else 413
            error = "invalid content length" if length < 0 else "body too large"
            self._json(status, {"ok": False, "error": error})
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "invalid JSON"})
            return
        if not isinstance(body, dict):
            self._json(400, {"ok": False, "error": "JSON object required"})
            return
        try:
            report = investigate(body, self.server.config)
        except BadRequest as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:
            print(f"investigation error: {type(exc).__name__}: {redact(str(exc)[:200])}", file=sys.stderr)
            self._json(500, {"ok": False, "error": "investigation failed"})
            return
        self._json(200, report)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # The web UI runs on its own local port; allow it to call this API.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} {fmt % args}")


class AppServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, config):
        super().__init__(address, Handler)
        self.config = config


def main() -> int:
    parser = argparse.ArgumentParser(description="Becuz server")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()

    config = load()
    host = args.host or config.server_host
    port = config.server_port if args.port is None else args.port
    server = AppServer((host, port), config)

    print(f"Becuz on http://{host}:{port}  (POST /run, GET /health)")
    if config.sample_mode:
        print("Sample mode is on: local data, rule-based judgement, no provider calls.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
