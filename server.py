from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from becuz.config import load
from becuz.investigate import BadRequest, confirm, investigate, new_run_id, parse, trace_events
from becuz.safety import redact

MAX_BODY = 1_000_000
RUN_PATH = re.compile(r"/runs/(inv-[0-9a-f]{10})")


class Handler(BaseHTTPRequestHandler):
    server_version = "Becuz/0.1"

    def do_GET(self) -> None:
        if self.path == "/health":
            config = self.server.config
            self._json(200, {"ok": True, "sample": config.sample_mode,
                             "providers": {"zetaris": config.has_zetaris, "nightshift": config.has_nightshift}})
            return
        match = RUN_PATH.fullmatch(self.path)
        if match:
            self._run_status(match.group(1))
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_OPTIONS(self) -> None:
        self._send(204, b"", "text/plain")  # CORS preflight for the web UI

    def do_POST(self) -> None:
        handlers = {"/run": self._run, "/runs": self._start_run, "/confirm": self._confirm}
        if self.path not in handlers:
            self._json(404, {"ok": False, "error": "not found"})
            return
        body = self._body()
        if body is not None:
            handlers[self.path](body)

    def _body(self) -> dict | None:
        """The request's JSON object, or None after answering with the error."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._json(400, {"ok": False, "error": "invalid content length"})
            return None
        if length < 0 or length > MAX_BODY:
            status = 400 if length < 0 else 413
            error = "invalid content length" if length < 0 else "body too large"
            self._json(status, {"ok": False, "error": error})
            return None
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "invalid JSON"})
            return None
        if not isinstance(body, dict):
            self._json(400, {"ok": False, "error": "JSON object required"})
            return None
        return body

    def _run(self, body: dict) -> None:
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

    def _start_run(self, body: dict) -> None:
        """Starts a run in the background and answers at once; poll GET /runs/<run_id> for steps and the report."""
        try:
            parse(body, self.server.config.sample_mode)  # a bad request is refused now, not after the wait
        except BadRequest as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        run_id = new_run_id()
        self.server.jobs[run_id] = {"status": "running"}
        threading.Thread(target=self.server.work, args=(run_id, body), daemon=True).start()
        self._json(202, {"run_id": run_id, "status": "running", "poll": f"/runs/{run_id}"})

    def _run_status(self, run_id: str) -> None:
        job = self.server.jobs.get(run_id)
        events = trace_events(run_id, self.server.config)
        if job is None and events is None:
            self._json(404, {"ok": False, "error": f"no run {run_id}"})
            return
        # A run started from the command line has a trace but no job here: its steps are all we have.
        job = job or {"status": "finished"}
        self._json(200, {"run_id": run_id, **job, "events": events or []})

    def _confirm(self, body: dict) -> None:
        try:
            memory_id = confirm(body.get("run_id"), body.get("cause_id"), self.server.config)
        except (BadRequest, KeyError) as exc:
            self._json(400, {"ok": False, "error": str(exc).strip("'")})
            return
        self._json(200, {"ok": True, "memory_id": memory_id})

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
        # shortcut: jobs live in memory and are lost on restart; fine for one server and a demo, not for many.
        self.jobs: dict[str, dict] = {}

    def work(self, run_id: str, body: dict) -> None:
        try:
            self.jobs[run_id] = {"status": "complete", "report": investigate(body, self.config, run_id=run_id)}
        except BadRequest as exc:  # the owner's own words, e.g. not enough records for that period
            self.jobs[run_id] = {"status": "failed", "error": str(exc)}
        except Exception as exc:
            print(f"investigation error: {type(exc).__name__}: {redact(str(exc)[:200])}", file=sys.stderr)
            self.jobs[run_id] = {"status": "failed", "error": "investigation failed"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Becuz server")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()

    config = load()
    host = args.host or config.server_host
    port = config.server_port if args.port is None else args.port
    server = AppServer((host, port), config)

    print(f"Becuz on http://{host}:{port}  (POST /run, POST /runs, GET /runs/<id>, POST /confirm, GET /health)")
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
