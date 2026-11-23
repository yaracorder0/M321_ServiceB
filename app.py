
"""Service B – Item Provider Service (Python Standard Library).

Implements the REST API interface strictly adhering to the OpenAPI 3.0 API contract.
"""
import json
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from contract import load_api_contract, validate_item_input
from models import Item
from service import InMemoryItemService, ItemServiceInterface

PORT = int(os.environ.get("PORT", 5000))

# Error & message constants
ERR_ITEM_NOT_FOUND = "Item not found"
ERR_INVALID_ID = "Invalid ID format"
ERR_ENDPOINT_NOT_FOUND = "Endpoint not found"
MSG_ID_MUST_BE_INT = "Item ID must be an integer."
PREFIX_ITEMS = "/api/items/"

# Default initial items
DEFAULT_ITEMS = [
    Item(id=1, name="Laptop", price=1299.90),
    Item(id=2, name="Monitor", price=349.00),
    Item(id=3, name="Keyboard", price=89.50),
]

# Instantiate service layer implementing ItemServiceInterface
item_service: ItemServiceInterface = InMemoryItemService(DEFAULT_ITEMS)

# Load OpenAPI contract
API_CONTRACT = load_api_contract()

SWAGGER_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Service B – API Contract (Swagger UI)</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    body { margin: 0; padding: 0; background-color: #fafafa; }
    .topbar { display: none; }
  </style>
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin></script>
<script>
  window.onload = () => {
    SwaggerUIBundle({
      url: '/openapi.json',
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
      ]
    });
  };
</script>
</body>
</html>
"""


class ContractAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler implementing the API contract for Service B."""

    item_id_pattern = re.compile(r"^/api/items/(\d+)$")

    # Helper methods for sending responses adhering to contract
    def send_json(self, status: int, data: any, headers: dict = None):
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def send_error_contract(self, status: int, error: str, detail: str = None):
        """Send standardized ErrorResponse adhering to API contract."""
        body = {"error": error}
        if detail:
            body["detail"] = detail
        self.send_json(status, body)

    def read_json_body(self):
        """Read and parse JSON body from incoming request."""
        content_length_str = self.headers.get("Content-Length")
        if not content_length_str:
            return None, "Missing Content-Length header or empty request body."
        try:
            length = int(content_length_str)
        except ValueError:
            return None, "Invalid Content-Length header."

        if length <= 0:
            return None, "Request body cannot be empty."

        try:
            raw_body = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw_body)
            return data, None
        except UnicodeDecodeError:
            return None, "Request body must be valid UTF-8 encoded string."
        except json.JSONDecodeError as exc:
            return None, f"Malformed JSON: {exc.msg}"

    def _serve_yaml_contract(self):
        yaml_path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "rb") as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/x-yaml; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error_contract(HTTPStatus.NOT_FOUND, ERR_ENDPOINT_NOT_FOUND, "openapi.yaml not found.")

    def _serve_docs_html(self):
        content = SWAGGER_UI_HTML.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _handle_get_single_item(self, path: str):
        match = self.item_id_pattern.match(path)
        if match:
            item_id = int(match.group(1))
            item = item_service.get_by_id(item_id)
            if item:
                self.send_json(HTTPStatus.OK, item.to_dict())
            else:
                self.send_error_contract(
                    HTTPStatus.NOT_FOUND,
                    ERR_ITEM_NOT_FOUND,
                    f"Item with id {item_id} does not exist.",
                )
        elif path.startswith(PREFIX_ITEMS):
            self.send_error_contract(
                HTTPStatus.BAD_REQUEST,
                ERR_INVALID_ID,
                MSG_ID_MUST_BE_INT,
            )
        else:
            self.send_error_contract(
                HTTPStatus.NOT_FOUND,
                ERR_ENDPOINT_NOT_FOUND,
                f"No route found for GET {path}",
            )

    # Route Handlers
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.send_json(HTTPStatus.OK, {"message": "Hello World from Service B"})
        elif path == "/health":
            self.send_json(HTTPStatus.OK, {"status": "UP", "service": "service-b"})
        elif path == "/openapi.json":
            self.send_json(HTTPStatus.OK, API_CONTRACT)
        elif path == "/openapi.yaml":
            self._serve_yaml_contract()
        elif path == "/docs":
            self._serve_docs_html()
        elif path == "/api/items":
            items = [item.to_dict() for item in item_service.get_all()]
            self.send_json(HTTPStatus.OK, items)
        else:
            self._handle_get_single_item(path)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/items":
            data, error = self.read_json_body()
            if error:
                self.send_error_contract(HTTPStatus.BAD_REQUEST, "Bad Request", error)
                return

            is_valid, validation_error, sanitized_data = validate_item_input(data)
            if not is_valid:
                self.send_error_contract(
                    HTTPStatus.BAD_REQUEST,
                    "Validation Error",
                    validation_error,
                )
                return

            created_item = item_service.create(
                name=sanitized_data["name"],
                price=sanitized_data["price"],
            )
            location_header = {"Location": f"/api/items/{created_item.id}"}
            self.send_json(HTTPStatus.CREATED, created_item.to_dict(), headers=location_header)
        else:
            self.send_error_contract(
                HTTPStatus.NOT_FOUND,
                ERR_ENDPOINT_NOT_FOUND,
                f"No route found for POST {path}",
            )

    def do_PUT(self):
        path = urlparse(self.path).path
        match = self.item_id_pattern.match(path)

        if match:
            item_id = int(match.group(1))
            data, error = self.read_json_body()
            if error:
                self.send_error_contract(HTTPStatus.BAD_REQUEST, "Bad Request", error)
                return

            is_valid, validation_error, sanitized_data = validate_item_input(data)
            if not is_valid:
                self.send_error_contract(
                    HTTPStatus.BAD_REQUEST,
                    "Validation Error",
                    validation_error,
                )
                return

            updated_item = item_service.update(
                item_id=item_id,
                name=sanitized_data["name"],
                price=sanitized_data["price"],
            )
            if updated_item:
                self.send_json(HTTPStatus.OK, updated_item.to_dict())
            else:
                self.send_error_contract(
                    HTTPStatus.NOT_FOUND,
                    ERR_ITEM_NOT_FOUND,
                    f"Item with id {item_id} does not exist.",
                )
        elif path.startswith(PREFIX_ITEMS):
            self.send_error_contract(
                HTTPStatus.BAD_REQUEST,
                ERR_INVALID_ID,
                MSG_ID_MUST_BE_INT,
            )
        else:
            self.send_error_contract(
                HTTPStatus.NOT_FOUND,
                ERR_ENDPOINT_NOT_FOUND,
                f"No route found for PUT {path}",
            )

    def do_DELETE(self):
        path = urlparse(self.path).path
        match = self.item_id_pattern.match(path)

        if match:
            item_id = int(match.group(1))
            deleted = item_service.delete(item_id)
            if deleted:
                self.send_json(HTTPStatus.OK, {"message": "Item deleted successfully"})
            else:
                self.send_error_contract(
                    HTTPStatus.NOT_FOUND,
                    ERR_ITEM_NOT_FOUND,
                    f"Item with id {item_id} does not exist.",
                )
        elif path.startswith(PREFIX_ITEMS):
            self.send_error_contract(
                HTTPStatus.BAD_REQUEST,
                ERR_INVALID_ID,
                MSG_ID_MUST_BE_INT,
            )
        else:
            self.send_error_contract(
                HTTPStatus.NOT_FOUND,
                ERR_ENDPOINT_NOT_FOUND,
                f"No route found for DELETE {path}",
            )


def run_server(port: int = PORT):
    server = HTTPServer(("", port), ContractAPIHandler)
    print(f"Service B läuft auf http://localhost:{port}")
    print(f"API Contract (JSON): http://localhost:{port}/openapi.json")
    print(f"Swagger UI Docs:     http://localhost:{port}/docs")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nService B gestoppt.")
        server.server_close()


if __name__ == "__main__":
    run_server(PORT)
