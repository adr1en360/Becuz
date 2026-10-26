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

    def test_the_old_scaffold_routes_are_gone(self) -> None:
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



class JobRouteTests(unittest.TestCase):
    """POST /runs, GET /runs/<id> and POST /confirm against a real sample-mode run."""

    def setUp(self) -> None:
        import tempfile
        from pathlib import Path

        self.tmp = tempfile.TemporaryDirectory()
        config = SimpleNamespace(sample_mode=True, has_zetaris=False, has_nightshift=False, ledger_path=None,
                                 trace_path=Path(self.tmp.name) / "trace.jsonl")
        self.server = AppServer(("127.0.0.1", 0), config)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    call = ServerTests.call

    def finished(self, run_id: str) -> dict:
        import time

        for _ in range(100):
            status, data = self.call("GET", f"/runs/{run_id}")
            job = json.loads(data)
            if job["status"] != "running":
                return job
            time.sleep(0.1)
        self.fail("the run did not finish")

    def test_a_started_run_can_be_polled_for_its_steps_and_report(self) -> None:
        status, data = self.call("POST", "/runs", {"question": "Why is my profit down?", "scenario": "s04"})
        self.assertEqual(status, 202)
        run_id = json.loads(data)["run_id"]
        job = self.finished(run_id)
        self.assertEqual(job["status"], "complete")
        self.assertEqual(job["report"]["run_id"], run_id)
        self.assertEqual({e["agent_name"] for e in job["events"]}, {"Planner", "Investigator", "Checker", "Writer"})

    def test_a_bad_request_is_refused_before_the_run_starts(self) -> None:
        status, data = self.call("POST", "/runs", {"question": ""})
        self.assertEqual(status, 400)
        status, data = self.call("POST", "/runs", {"question": "What is the weather in Lagos?"})
        self.assertEqual(status, 400)
        self.assertIn("How is my shop doing?", json.loads(data)["error"])  # a friendly reply with examples
        self.assertEqual(self.server.jobs, {})

    def test_confirm_stores_a_supported_cause_and_refuses_others(self) -> None:
        run_id = json.loads(self.call("POST", "/runs", {"question": "Why is my profit down?", "scenario": "s04"})[1])["run_id"]
        self.finished(run_id)
        status, data = self.call("POST", "/confirm", {"run_id": run_id, "cause_id": "transfer_leakage"})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(data)["memory_id"].startswith("mem-"))
        for bad in ({"run_id": run_id, "cause_id": "pos_charge_rise"}, {"run_id": run_id, "cause_id": "no_such_cause"},
                    {"run_id": "../../etc/passwd", "cause_id": "transfer_leakage"}, {}):
            with self.subTest(bad=bad):
                self.assertEqual(self.call("POST", "/confirm", bad)[0], 400)

    def test_unknown_or_malformed_run_ids_are_not_found(self) -> None:
        self.assertEqual(self.call("GET", "/runs/inv-0000000000")[0], 404)
        self.assertEqual(self.call("GET", "/runs/../../etc/passwd")[0], 404)


if __name__ == "__main__":
    unittest.main()
