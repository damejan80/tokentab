"""The web dashboard: the same report, drawn as an invoice instead of ASCII.

Built on the standard library's http.server so there's no web framework to pull
in. It reads from disk on every request (the data's tiny, so no reason to cache
and risk showing something stale), binds to localhost only, and never touches the
network.
"""

from __future__ import annotations

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from ..providers import collect_all
from ..report.aggregate import build_report, parse_range
from ..report.serialize import report_to_dict
from .page import render_page


def _make_handler(default_period: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # quiet — we don't want a request log spewing in the terminal

        def do_GET(self):
            parsed = urlparse(self.path)

            try:
                if parsed.path == "/api/report":
                    qs = parse_qs(parsed.query)
                    period = (qs.get("period") or [default_period])[0]
                    records = collect_all()
                    report = build_report(records, parse_range(period))
                    body = json.dumps(report_to_dict(report)).encode("utf-8")
                    self._send(200, "application/json", body)
                    return

                if parsed.path == "/":
                    self._send(200, "text/html; charset=utf-8", render_page().encode("utf-8"))
                    return

                self._send(404, "text/plain", b"not found")
            except Exception as err:  # never let one bad request kill the server
                self._send(500, "text/plain", f"error: {err}".encode("utf-8"))

        def _send(self, code: int, ctype: str, body: bytes):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def start_web(port: int, open_browser: bool, period: str) -> None:
    handler = _make_handler(period)

    # port 0 (or a taken port) -> let the OS pick a free one
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)

    actual_port = server.server_address[1]
    link = f"http://localhost:{actual_port}"
    print(f"tokentab is running at {link}")
    print("press ctrl-c to stop")

    if open_browser:
        threading.Timer(0.4, lambda: _safe_open(link)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
        server.shutdown()


def _safe_open(link: str) -> None:
    try:
        webbrowser.open(link)
    except Exception:
        pass  # opening a browser is a nicety, not a requirement
