from __future__ import annotations

import http.client
import json
import socket
import threading
import unittest
from types import SimpleNamespace

from server import AppServer


class FakeAgent:
    config = SimpleNamespace(
        sample_mode=True,
        has_zetaris=False,
        has_nightshift=False,
    )

    def __init__(self, fail: bool = False, unserializable: bool = False):
        self.fail = fail
        self.unserializable = unserializable

    def run(self, request: str) -> dict:
        if self.fail:
            raise RuntimeError("boom")
        if self.unserializable:
            return {"ok": True, "bad": {1}}
        return {"ok": True, "request": request}


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = AppServer(("127.0.0.1", 0), FakeAgent())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def call(self, method: str, path: str, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        try:
            headers = {"Content-Type": "application/json"} if body is not None else {}
            payload = json.dumps(body) if body is not None else None
            connection.request(method, path, body=payload, headers=headers)
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def test_health_and_ask(self) -> None:
        status, data = self.call("GET", "/health")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(data)["ok"])

        status, data = self.call("POST", "/ask", {"request": "hello"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["request"], "hello")

    def test_bad_requests(self) -> None:
        status, _ = self.call("POST", "/ask", {"request": None})
        self.assertEqual(status, 400)
        status, _ = self.call("POST", "/ask", {"request": "x" * 4001})
        self.assertEqual(status, 400)

    def test_negative_length(self) -> None:
        with socket.create_connection(("127.0.0.1", self.port), timeout=2) as sock:
            sock.sendall(
                b"POST /ask HTTP/1.1\r\nHost: localhost\r\nContent-Length: -1\r\n\r\n"
            )
            data = sock.recv(4096)
        self.assertIn(b"400", data)

    def test_agent_error(self) -> None:
        self.server.agent = FakeAgent(fail=True)
        status, data = self.call("POST", "/ask", {"request": "hello"})
        self.assertEqual(status, 500)
        self.assertFalse(json.loads(data)["ok"])

    def test_unserializable_result(self) -> None:
        self.server.agent = FakeAgent(unserializable=True)
        status, data = self.call("POST", "/ask", {"request": "hello"})
        self.assertEqual(status, 500)
        self.assertFalse(json.loads(data)["ok"])


if __name__ == "__main__":
    unittest.main()
