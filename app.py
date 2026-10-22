"""
WaveNxD AI Sales Representative - Server Application
===================================================
A lightweight, zero-dependency HTTP server and REST API for the WaveNxD Sales Representative.
Built using standard library http.server, supporting:
- /: ChatGPT-style Web Interface
- /static/*: Static styling and interactive scripts
- /api/catalog: Single Source of Truth product catalog JSON
- /api/chat: Multi-turn sales conversation endpoint (SalesGPT stage-aware agent)
- /api/send_quote: Real Email Quotation Dispatch (SMTP/Gmail support)
- /api/calendar_invite: RFC-5545 .ics Calendar Invite Generation and Download
- /api/reset: Reset conversation session
"""

import json
import mimetypes
import os
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict

from salesgpt.agent import SalesAgent
from salesgpt.catalog import WaveNxDCatalog
from salesgpt.tools import (
    generate_ics_calendar_invite,
    send_enquiry_email,
    send_quotation_email,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_env_file():
    """Loads key-value pairs from .env if present."""
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env_file()

catalog = WaveNxDCatalog()
sales_agent = SalesAgent(catalog_obj=catalog)


class WaveNxDHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Any, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath: str, content_type: str = None):
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            self.send_error(404, "File not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        if not content_type:
            content_type = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            template_path = os.path.join(BASE_DIR, "templates", "index.html")
            self._send_file(template_path, "text/html; charset=utf-8")

        elif path == "/api/catalog":
            self._send_json(catalog.data)

        elif path == "/api/calendar_invite":
            client_name = query.get("name", ["Valued Client"])[0]
            company = query.get("company", ["Client Organization"])[0]
            slot = query.get("slot", ["Tomorrow at 11:00 AM"])[0]
            email = query.get("email", ["client@example.com"])[0]

            ics_data = generate_ics_calendar_invite(client_name, company, slot, email).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/calendar; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="wavenxd-followup.ics"')
            self.send_header("Content-Length", str(len(ics_data)))
            self.end_headers()
            self.wfile.write(ics_data)

        elif path.startswith("/static/"):
            rel = path.lstrip("/")
            target = os.path.abspath(os.path.join(BASE_DIR, rel))
            static_dir = os.path.abspath(os.path.join(BASE_DIR, "static"))
            if target.startswith(static_dir):
                self._send_file(target)
            else:
                self.send_error(403, "Forbidden")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(raw)
        except Exception:
            data = {}

        if path == "/api/chat":
            messages = data.get("messages", [])
            api_key = (data.get("api_key") or "").strip() or None
            provider = (data.get("provider") or "").strip() or None
            result = sales_agent.run(messages, api_key=api_key, provider=provider)
            self._send_json(result)

        elif path == "/api/send_quote":
            recipient = data.get("email", "")
            client_name = data.get("client_name", "")
            company = data.get("company", "")
            nozzle_name = data.get("nozzle_name", "WaveNxD Ultrasonic Nozzle")
            specs = data.get("specs", "")
            slot = data.get("callback_slot", "")

            email_result = send_quotation_email(
                recipient_email=recipient,
                client_name=client_name,
                company=company,
                nozzle_name=nozzle_name,
                specs_summary=specs,
                callback_slot=slot,
            )
            self._send_json(email_result)

        elif path == "/api/send_enquiry":
            required_fields = (
                "client_name",
                "company",
                "email",
                "phone",
                "callback_slot",
            )
            if not isinstance(data, dict):
                self._send_json(
                    {"status": "error", "message": "Invalid request body."},
                    status=400,
                )
                return

            enquiry = {}
            for field in required_fields:
                value = data.get(field)
                if not isinstance(value, str) or not value.strip():
                    self._send_json(
                        {
                            "status": "error",
                            "message": f"{field} is required.",
                        },
                        status=400,
                    )
                    return
                enquiry[field] = value.strip()

            if (
                len(enquiry["email"]) > 254
                or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", enquiry["email"])
            ):
                self._send_json(
                    {"status": "error", "message": "Enter a valid email address."},
                    status=400,
                )
                return

            phone_digits = re.sub(r"\D", "", enquiry["phone"])
            if not 7 <= len(phone_digits) <= 15:
                self._send_json(
                    {"status": "error", "message": "Enter a valid phone number."},
                    status=400,
                )
                return

            limits = {
                "client_name": 200,
                "company": 200,
                "email": 254,
                "phone": 40,
                "callback_slot": 200,
            }
            if any(len(enquiry[field]) > limit for field, limit in limits.items()):
                self._send_json(
                    {"status": "error", "message": "One or more fields are too long."},
                    status=400,
                )
                return

            conversation = data.get("conversation", "")
            if not isinstance(conversation, str) or len(conversation) > 12000:
                self._send_json(
                    {"status": "error", "message": "Conversation details are invalid or too long."},
                    status=400,
                )
                return

            email_result = send_enquiry_email(
                client_name=enquiry["client_name"],
                company=enquiry["company"],
                email=enquiry["email"],
                phone=enquiry["phone"],
                callback_slot=enquiry["callback_slot"],
                conversation=conversation,
            )
            status_code = 200 if email_result["status"] == "success" else 503
            self._send_json(email_result, status=status_code)

        elif path == "/api/reset":
            result = sales_agent.run([{"role": "user", "content": "reset"}])
            self._send_json(result)

        else:
            self.send_error(404, "Not Found")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), WaveNxDHandler)
    print(f"==================================================")
    print(f"WaveNxD AI Sales Representative (SalesGPT Engine)")
    print(f"Server running at: http://localhost:{port}")
    print(f"==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
