from __future__ import annotations

import http.client
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from local_runtime import (  # noqa: E402
    DEFAULT_ALLOWED_HOSTS,
    RuntimeHandler,
    _host_is_allowed,
    _normalize_host_header,
)


class QuietRuntimeHandler(RuntimeHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class HostHeaderUnitTests(unittest.TestCase):
    def test_normalizes_loopback_hosts_and_ports(self) -> None:
        self.assertEqual(_normalize_host_header("localhost:4327"), "localhost")
        self.assertEqual(_normalize_host_header("LOCALHOST."), "localhost")
        self.assertEqual(_normalize_host_header("[::1]:4327"), "::1")

    def test_rejects_malformed_or_untrusted_hosts(self) -> None:
        self.assertIsNone(_normalize_host_header(""))
        self.assertIsNone(_normalize_host_header("localhost/path"))
        self.assertIsNone(_normalize_host_header("user@localhost"))
        self.assertFalse(_host_is_allowed("attacker.example", DEFAULT_ALLOWED_HOSTS))
        self.assertFalse(_host_is_allowed("localhost.attacker.example", DEFAULT_ALLOWED_HOSTS))
        self.assertFalse(_host_is_allowed("0.0.0.0", DEFAULT_ALLOWED_HOSTS))


class HostHeaderIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        (root / "index.html").write_text("<!doctype html><title>Test</title>")
        handler = partial(
            QuietRuntimeHandler,
            directory=str(root),
            runtime_config={},
            allowed_hosts=DEFAULT_ALLOWED_HOSTS,
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(self, host_header: str) -> tuple[int, str]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            connection.request(
                "GET",
                "/runtime/health",
                headers={"Host": host_header},
            )
            response = connection.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            connection.close()

    def test_accepts_localhost_with_port(self) -> None:
        status, body = self.request(f"localhost:{self.port}")
        self.assertEqual(status, 200)
        self.assertIn('"ok": true', body)

    def test_rejects_dns_rebinding_host(self) -> None:
        status, body = self.request("attacker.example")
        self.assertEqual(status, 421)
        self.assertIn("Host header rejected", body)


if __name__ == "__main__":
    unittest.main()
