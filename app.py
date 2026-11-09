"""Service B – Hello World (Python, nur Standardbibliothek)."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", 5000))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = {"status": "UP", "service": "service-b"}
        else:
            body = {"message": "Hello World from Service B"}
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"Service B läuft auf http://localhost:{PORT}")
    HTTPServer(("", PORT), Handler).serve_forever()
