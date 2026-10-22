from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from base.config import load
from base.providers import redact
from base.runtime import build_agent

MAX_BODY = 1_000_000
MAX_REQUEST = 4000

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Becuz</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #1d1d1b;
      --muted: #66665f;
      --paper: #f4f4ee;
      --card: #ffffff;
      --line: #d9d9d0;
      --accent: #1f5f4a;
      --accent-ink: #ffffff;
      --code: #1d1d1b;
      --code-ink: #f2f2ec;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--paper);
      color: var(--ink);
      font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif;
    }
    main {
      width: min(860px, calc(100% - 32px));
      margin: 48px auto;
    }
    h1 {
      margin: 0 0 6px;
      font-size: 32px;
      letter-spacing: -0.02em;
    }
    p { margin: 0 0 20px; color: var(--muted); }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 20px;
    }
    label { display: block; font-weight: 600; margin-bottom: 8px; }
    textarea {
      width: 100%;
      min-height: 120px;
      resize: vertical;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      font: inherit;
      color: var(--ink);
      background: #fbfbf8;
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-top: 12px;
    }
    button {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px 14px;
      background: #fbfbf8;
      color: var(--ink);
      font: inherit;
      cursor: pointer;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: var(--accent-ink);
      font-weight: 600;
    }
    button:hover { filter: brightness(0.97); }
    pre {
      margin: 20px 0 0;
      padding: 16px;
      min-height: 120px;
      overflow: auto;
      border-radius: 8px;
      background: var(--code);
      color: var(--code-ink);
      font: 13px/1.55 ui-monospace, "Cascadia Code", Consolas, monospace;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .hint { margin-top: 10px; font-size: 13px; color: var(--muted); }
  </style>
</head>
<body>
  <main>
    <h1>Becuz</h1>
    <p>Scaffold UI. Replace this page when the idea is ready.</p>
    <section class="card">
      <label for="q">Request</label>
      <textarea id="q" placeholder="SELECT 1 AS one"></textarea>
      <div class="row">
        <button class="primary" id="run" type="button">Run</button>
        <button type="button" data-example="SELECT 1 AS one">SQL example</button>
        <button type="button" data-example="Reply with the single word: ready">Model example</button>
      </div>
      <div class="hint">API: POST /ask &middot; GET /health</div>
      <pre id="out" aria-live="polite">Ready.</pre>
    </section>
  </main>
  <script>
    const input = document.getElementById("q");
    const output = document.getElementById("out");
    const run = document.getElementById("run");

    document.querySelectorAll("[data-example]").forEach((button) => {
      button.addEventListener("click", () => {
        input.value = button.dataset.example;
        input.focus();
      });
    });

    async function ask() {
      const request = input.value.trim();
      if (!request) {
        output.textContent = "Enter a request.";
        return;
      }
      output.textContent = "Running...";
      try {
        const response = await fetch("/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ request }),
        });
        const data = await response.json();
        output.textContent = JSON.stringify(data, null, 2);
      } catch (error) {
        output.textContent = String(error);
      }
    }

    run.addEventListener("click", ask);
    input.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") ask();
    });
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "OpenAgent/0.1"

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if self.path == "/health":
            config = self.server.agent.config
            self._json(
                200,
                {
                    "ok": True,
                    "sample": config.sample_mode,
                    "providers": {
                        "zetaris": config.has_zetaris,
                        "nightshift": config.has_nightshift,
                    },
                },
            )
            return
        if self.path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/ask":
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
        value = body.get("request")
        if not isinstance(value, str) or not value.strip():
            self._json(400, {"ok": False, "error": "request is required"})
            return
        request = value.strip()
        if len(request) > MAX_REQUEST:
            self._json(400, {"ok": False, "error": "request too long"})
            return
        try:
            result = self.server.agent.run(request)
            body = json.dumps(result, ensure_ascii=True, indent=2).encode("utf-8")
        except Exception as exc:
            print(
                f"agent error: {type(exc).__name__}: {redact(str(exc)[:200])}",
                file=sys.stderr,
            )
            self._json(500, {"ok": False, "error": "agent failed"})
            return
        self._send(200, body, "application/json; charset=utf-8")

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} {fmt % args}")


class AppServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, agent):
        super().__init__(address, Handler)
        self.agent = agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Becuz server")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()

    config = load()
    agent = build_agent(config)
    host = args.host or config.server_host
    port = config.server_port if args.port is None else args.port
    server = AppServer((host, port), agent)

    print(f"Becuz on http://{host}:{port}")
    if config.sample_mode:
        print("Sample mode is on: no provider calls.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
