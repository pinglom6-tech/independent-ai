#!/usr/bin/env python3
"""Same-origin authenticated HTML UI and local model API gateway."""
import base64
import hmac
import json
import os
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PASSWORD = os.environ.get("CHAT_UI_PASSWORD", "")
MODEL = os.environ.get("MODEL_ID", "Qwen/Qwen3.5-27B-FP8")
UPSTREAM = "http://127.0.0.1:8000/v1/chat/completions"
if not PASSWORD:
    raise SystemExit("CHAT_UI_PASSWORD is required")

class Handler(BaseHTTPRequestHandler):
    def authorized(self):
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            raw = base64.b64decode(header[6:], validate=True).decode()
            user, password = raw.split(":", 1)
            return hmac.compare_digest(user, "owner") and hmac.compare_digest(password, PASSWORD)
        except (ValueError, UnicodeError):
            return False

    def reply(self, code, payload, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def check(self):
        if self.authorized():
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Independent AI"')
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        return False

    def do_GET(self):
        if not self.check():
            return
        if self.path in ("/", "/index.html"):
            self.reply(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/health":
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=3) as response:
                    ok = response.status == 200
            except Exception:
                ok = False
            self.reply(200 if ok else 503, json.dumps({"model_ready": ok}).encode())
        else:
            self.reply(404, b'{"error":"not found"}')

    def do_POST(self):
        if not self.check():
            return
        if self.path != "/v1/chat/completions":
            self.reply(404, b'{"error":"not found"}')
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 131072:
                self.reply(413, b'{"error":"invalid request size"}')
                return
            body = json.loads(self.rfile.read(size))
            if not isinstance(body.get("messages"), list):
                raise ValueError("messages must be a list")
            body["model"] = MODEL
            body["stream"] = False
            req = urllib.request.Request(UPSTREAM, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=180) as response:
                data = response.read(2097152)
                self.reply(200, data)
        except urllib.error.HTTPError as exc:
            self.reply(502, json.dumps({"error": "model returned HTTP " + str(exc.code)}).encode())
        except (urllib.error.URLError, TimeoutError):
            self.reply(503, b'{"error":"model unavailable"}')
        except (ValueError, json.JSONDecodeError) as exc:
            self.reply(400, json.dumps({"error": str(exc)}).encode())
        except Exception:
            self.reply(500, b'{"error":"internal gateway error"}')

ThreadingHTTPServer(("0.0.0.0", 8888), Handler).serve_forever()
