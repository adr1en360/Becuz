from __future__ import annotations

import http.client
import json
import socket
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from server import AppServer

CONFIG = SimpleNamespace(sample_mode=True, has_zetaris=False, has_nightshift=False)


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = AppServer(("127.0.0.1", 0), CONFIG)
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

    def test_health(self) -> None:
        status, data = self.call("GET", "/health")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(data)["sample"])

    def test_only_run_and_health_exist(self) -> None:
        self.assertEqual(self.call("POST", "/ask", {"request": "hello"})[0], 404)
        self.assertEqual(self.call("GET", "/")[0], 404)

    def test_run_rejects_a_bad_request_and_allows_the_web_ui(self) -> None:
        status, data = self.call("POST", "/run", {"question": ""})
        self.assertEqual(status, 400)
        self.assertIn("question", json.loads(data)["error"])
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        try:
            connection.request("OPTIONS", "/run")
            response = connection.getresponse()
            self.assertEqual(response.status, 204)
            self.assertEqual(response.getheader("Access-Control-Allow-Origin"), "*")
        finally:
            connection.close()

    def test_bad_bodies(self) -> None:
        self.assertEqual(self.call("POST", "/run", ["not", "an", "object"])[0], 400)
        with socket.create_connection(("127.0.0.1", self.port), timeout=2) as sock:
            sock.sendall(b"POST /run HTTP/1.1\r\nHost: localhost\r\nContent-Length: -1\r\n\r\n")
            data = sock.recv(4096)
        self.assertIn(b"400", data)

    def test_a_crash_returns_500_without_details(self) -> None:
        with patch("server.investigate", side_effect=RuntimeError("secret detail")):
            status, data = self.call("POST", "/run", {"question": "Why is my profit down?"})
        self.assertEqual(status, 500)
        self.assertEqual(json.loads(data)["error"], "investigation failed")


if __name__ == "__main__":
    unittest.main()
