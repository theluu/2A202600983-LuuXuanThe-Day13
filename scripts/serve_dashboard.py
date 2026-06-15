"""Phục vụ dashboard.html cùng origin với API.

Chạy app trước (uvicorn app.main:app --port 8013), rồi:
    python scripts/serve_dashboard.py
Mở: http://127.0.0.1:8014/dashboard.html

Server này phục vụ file tĩnh của repo VÀ proxy /metrics -> API 8013
để dashboard fetch /metrics cùng origin (tránh chặn CORS).
"""
from __future__ import annotations

import http.server
import socketserver
import urllib.request
from pathlib import Path

PORT = 8014
API = "http://127.0.0.1:8013"
ROOT = Path(__file__).resolve().parent.parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/metrics") or self.path.startswith("/health"):
            try:
                with urllib.request.urlopen(f"{API}{self.path}", timeout=5) as resp:
                    body = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:  # noqa: BLE001
                self.send_error(502, f"API not reachable: {exc}")
            return
        super().do_GET()

    def log_message(self, *args):  # giữ output gọn
        return


if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Dashboard: http://127.0.0.1:{PORT}/dashboard.html  (proxy /metrics -> {API})")
        httpd.serve_forever()
