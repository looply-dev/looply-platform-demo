"""HTTP API (standard library http.server only).

The API layer does three things: parse requests, call LendingService, and turn results or errors into JSON.
It must not import the storage layer.
"""

import json
import re
import sqlite3
from dataclasses import asdict
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qsl, urlsplit

from lending.api.reports import overdue_report

from lending.domain.errors import LendingError, NotFound
from lending.services.lending_service import LendingService

# Route table: (HTTP method, path regex, handler method name)
ROUTES: list[tuple[str, re.Pattern[str], str]] = [
    ("GET", re.compile(r"^/health$"), "health"),
    ("GET", re.compile(r"^/members/(?P<member_id>\d+)/loans$"), "member_loans"),
    ("POST", re.compile(r"^/loans$"), "borrow"),
    ("POST", re.compile(r"^/loans/(?P<loan_id>\d+)/return$"), "return_book"),
    ("POST", re.compile(r"^/loans/(?P<loan_id>\d+)/renew$"), "renew"),
    ("GET", re.compile(r"^/reports/overdue$"), "overdue"),
]


def _json_default(value: Any) -> Any:
    """Let json.dumps serialize date values."""
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"cannot serialize {type(value).__name__}")


class Endpoints:
    """One handler per route. Each returns (status, body)."""

    def __init__(self, service: LendingService, report_conn: sqlite3.Connection | None = None):
        self._service = service
        self._report_conn = report_conn

    def health(self, body: dict) -> tuple[int, Any]:
        return 200, {"status": "ok"}

    def member_loans(self, body: dict, member_id: str) -> tuple[int, Any]:
        loans = self._service.member_loans(int(member_id))
        return 200, [asdict(loan) for loan in loans]

    def borrow(self, body: dict) -> tuple[int, Any]:
        try:
            member_id, book_id = int(body["member_id"]), int(body["book_id"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("member_id and book_id must be integers")
        return 201, asdict(self._service.borrow(member_id, book_id))

    def return_book(self, body: dict, loan_id: str) -> tuple[int, Any]:
        receipt = self._service.return_book(int(loan_id))
        return 200, {"loan": asdict(receipt.loan), "late_fee_cents": receipt.late_fee_cents}

    def renew(self, body: dict, loan_id: str) -> tuple[int, Any]:
        return 200, asdict(self._service.renew(int(loan_id)))

    def overdue(self, body: dict) -> tuple[int, Any]:
        if self._report_conn is None:
            return 503, {"error": "reports are not configured"}
        return 200, overdue_report(self._report_conn, date.today(), body.get("member"))


def make_handler(
    service: LendingService, report_conn: sqlite3.Connection | None = None
) -> type[BaseHTTPRequestHandler]:
    """Build a request handler class bound to the service (http.server takes a class, not an instance)."""
    endpoints = Endpoints(service, report_conn)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def log_message(self, format: str, *args: Any) -> None:
            # Keep test output quiet
            pass

        def _dispatch(self, method: str) -> None:
            """Match a route and map domain errors to HTTP status codes."""
            url = urlsplit(self.path)
            path = url.path
            for route_method, pattern, name in ROUTES:
                match = pattern.match(path)
                if route_method == method and match:
                    fn: Callable[..., tuple[int, Any]] = getattr(endpoints, name)
                    try:
                        # GET requests have no body, so pass the query string as params
                        params = self._read_json() if method == "POST" else dict(parse_qsl(url.query))
                        status, payload = fn(params, **match.groupdict())
                    except NotFound as exc:
                        status, payload = 404, {"error": str(exc)}
                    except LendingError as exc:
                        status, payload = 409, {"error": str(exc)}
                    except ValueError as exc:
                        status, payload = 400, {"error": str(exc)}
                    self._send(status, payload)
                    return
            self._send(404, {"error": f"no route for {method} {path}"})

        def _read_json(self) -> dict:
            """Read the JSON request body. Return an empty dict when there is no body."""
            length = int(self.headers.get("Content-Length") or 0)
            if length == 0:
                return {}
            try:
                return json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                raise ValueError("request body must be valid JSON")

        def _send(self, status: int, payload: Any) -> None:
            data = json.dumps(payload, default=_json_default).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def create_server(
    service: LendingService,
    host: str = "127.0.0.1",
    port: int = 8000,
    report_conn: sqlite3.Connection | None = None,
) -> ThreadingHTTPServer:
    """Create (but do not start) the HTTP server. port=0 lets the OS pick a free port."""
    return ThreadingHTTPServer((host, port), make_handler(service, report_conn))
