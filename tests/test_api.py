import json
import threading
import unittest
import urllib.error
import urllib.request

from lending.api.server import create_server
from tests.helpers import make_env


class ApiTest(unittest.TestCase):
    """Starts a real HTTP server on a random port and sends requests with urllib."""

    def setUp(self):
        self.service, self.repo, self.clock = make_env()
        self.member = self.repo.add_member("Alice")
        self.book = self.repo.add_book("SICP", "Abelson", 1)
        self.server = create_server(self.service, port=0)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def request(self, method, path, body=None):
        """Send a request and return (status, json). 4xx/5xx responses are returned, not raised."""
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def test_health(self):
        self.assertEqual(self.request("GET", "/health"), (200, {"status": "ok"}))

    def test_borrow_and_return_flow(self):
        status, loan = self.request("POST", "/loans", {"member_id": self.member.id, "book_id": self.book.id})
        self.assertEqual(status, 201)
        status, receipt = self.request("POST", f"/loans/{loan['id']}/return")
        self.assertEqual(status, 200)
        self.assertEqual(receipt["late_fee_cents"], 0)

    def test_error_mapping(self):
        self.assertEqual(self.request("POST", "/loans", {"member_id": "x"})[0], 400)
        self.assertEqual(self.request("GET", "/members/999/loans")[0], 404)
        self.request("POST", "/loans", {"member_id": self.member.id, "book_id": self.book.id})
        other = self.repo.add_member("Bob")
        self.assertEqual(self.request("POST", "/loans", {"member_id": other.id, "book_id": self.book.id})[0], 409)


if __name__ == "__main__":
    unittest.main()
