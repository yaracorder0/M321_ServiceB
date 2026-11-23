"""Automated contract & interface compliance tests for Service B.

Runs with Python standard library unittest without any external dependencies.
"""
import json
import threading
import unittest
import urllib.request
from http import HTTPStatus
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import ContractAPIHandler, item_service
from contract import load_api_contract, validate_item_input
from models import Item
from service import InMemoryItemService, ItemServiceInterface


class TestItemService(unittest.TestCase):
    """Test interface contract and in-memory implementation."""

    def setUp(self):
        self.service: ItemServiceInterface = InMemoryItemService([
            Item(id=1, name="Test Item", price=19.99)
        ])

    def test_implements_interface(self):
        self.assertIsInstance(self.service, ItemServiceInterface)

    def test_get_all(self):
        items = self.service.get_all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "Test Item")

    def test_get_by_id_found(self):
        item = self.service.get_by_id(1)
        self.assertIsNotNone(item)
        self.assertEqual(item.id, 1)

    def test_get_by_id_not_found(self):
        item = self.service.get_by_id(999)
        self.assertIsNone(item)

    def test_create(self):
        new_item = self.service.create("New Item", 50.0)
        self.assertEqual(new_item.id, 2)
        self.assertEqual(new_item.name, "New Item")
        self.assertEqual(new_item.price, 50.0)
        self.assertEqual(len(self.service.get_all()), 2)

    def test_update_existing(self):
        updated = self.service.update(1, "Updated Name", 29.99)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.name, "Updated Name")
        self.assertEqual(updated.price, 29.99)

    def test_update_not_found(self):
        updated = self.service.update(999, "None", 10.0)
        self.assertIsNone(updated)

    def test_delete_existing(self):
        deleted = self.service.delete(1)
        self.assertTrue(deleted)
        self.assertIsNone(self.service.get_by_id(1))

    def test_delete_not_found(self):
        deleted = self.service.delete(999)
        self.assertFalse(deleted)


class TestContractValidation(unittest.TestCase):
    """Test validation rules defined in the API contract."""

    def test_valid_input(self):
        is_valid, error, data = validate_item_input({"name": "Mouse", "price": 49.95})
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertEqual(data["name"], "Mouse")
        self.assertEqual(data["price"], 49.95)

    def test_missing_name(self):
        is_valid, error, _ = validate_item_input({"price": 49.95})
        self.assertFalse(is_valid)
        self.assertIn("Missing required field: 'name'", error)

    def test_empty_name(self):
        is_valid, error, _ = validate_item_input({"name": "   ", "price": 49.95})
        self.assertFalse(is_valid)
        self.assertIn("non-empty string", error)

    def test_missing_price(self):
        is_valid, error, _ = validate_item_input({"name": "Mouse"})
        self.assertFalse(is_valid)
        self.assertIn("Missing required field: 'price'", error)

    def test_negative_price(self):
        is_valid, error, _ = validate_item_input({"name": "Mouse", "price": -5.0})
        self.assertFalse(is_valid)
        self.assertIn("greater than 0", error)

    def test_bool_price_rejected(self):
        # Python bool is subclass of int, should be rejected
        is_valid, error, _ = validate_item_input({"name": "Mouse", "price": True})
        self.assertFalse(is_valid)
        self.assertIn("valid number", error)


class TestHttpApiContract(unittest.TestCase):
    """End-to-end HTTP tests verifying endpoints against the API contract."""

    @classmethod
    def setUpClass(cls):
        # Start server on dynamic port (port=0 lets OS pick free port)
        cls.server = HTTPServer(("localhost", 0), ContractAPIHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://localhost:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

        # Disable proxy for local test requests
        proxy_handler = urllib.request.ProxyHandler({})
        cls.opener = urllib.request.build_opener(proxy_handler)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_root(self):
        with self.opener.open(f"{self.base_url}/") as res:
            self.assertEqual(res.status, HTTPStatus.OK)
            data = json.loads(res.read().decode())
            self.assertIn("message", data)

    def test_get_health(self):
        with self.opener.open(f"{self.base_url}/health") as res:
            self.assertEqual(res.status, HTTPStatus.OK)
            data = json.loads(res.read().decode())
            self.assertEqual(data.get("status"), "UP")
            self.assertEqual(data.get("service"), "service-b")

    def test_get_openapi_contract(self):
        with self.opener.open(f"{self.base_url}/openapi.json") as res:
            self.assertEqual(res.status, HTTPStatus.OK)
            spec = json.loads(res.read().decode())
            self.assertEqual(spec.get("openapi"), "3.0.3")
            self.assertIn("/api/items", spec.get("paths", {}))
            self.assertIn("Item", spec.get("components", {}).get("schemas", {}))

    def test_get_docs_swagger_ui(self):
        with self.opener.open(f"{self.base_url}/docs") as res:
            self.assertEqual(res.status, HTTPStatus.OK)
            content = res.read().decode()
            self.assertIn("swagger-ui", content)

    def test_get_items(self):
        with self.opener.open(f"{self.base_url}/api/items") as res:
            self.assertEqual(res.status, HTTPStatus.OK)
            items = json.loads(res.read().decode())
            self.assertIsInstance(items, list)
            self.assertGreater(len(items), 0)
            first = items[0]
            self.assertIn("id", first)
            self.assertIn("name", first)
            self.assertIn("price", first)

    def test_get_item_by_id(self):
        with self.opener.open(f"{self.base_url}/api/items/1") as res:
            self.assertEqual(res.status, HTTPStatus.OK)
            item = json.loads(res.read().decode())
            self.assertEqual(item["id"], 1)

    def test_get_item_not_found(self):
        with self.assertRaises(HTTPError) as ctx:
            self.opener.open(f"{self.base_url}/api/items/99999")
        self.assertEqual(ctx.exception.code, HTTPStatus.NOT_FOUND)
        body = json.loads(ctx.exception.read().decode())
        self.assertIn("error", body)

    def test_post_item_valid(self):
        payload = json.dumps({"name": "Webcam HD", "price": 79.90}).encode("utf-8")
        req = Request(
            f"{self.base_url}/api/items",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener.open(req) as res:
            self.assertEqual(res.status, HTTPStatus.CREATED)
            self.assertTrue(res.headers.get("Location").startswith("/api/items/"))
            created = json.loads(res.read().decode())
            self.assertEqual(created["name"], "Webcam HD")
            self.assertEqual(created["price"], 79.90)
            self.assertIn("id", created)

    def test_post_item_invalid(self):
        # Missing price
        payload = json.dumps({"name": "No price item"}).encode("utf-8")
        req = Request(
            f"{self.base_url}/api/items",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            self.opener.open(req)
        self.assertEqual(ctx.exception.code, HTTPStatus.BAD_REQUEST)
        body = json.loads(ctx.exception.read().decode())
        self.assertEqual(body.get("error"), "Validation Error")

    def test_put_item_valid(self):
        payload = json.dumps({"name": "Laptop Pro", "price": 1499.00}).encode("utf-8")
        req = Request(
            f"{self.base_url}/api/items/1",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with self.opener.open(req) as res:
            self.assertEqual(res.status, HTTPStatus.OK)
            updated = json.loads(res.read().decode())
            self.assertEqual(updated["name"], "Laptop Pro")
            self.assertEqual(updated["price"], 1499.00)

    def test_delete_item(self):
        # Create item to delete
        payload = json.dumps({"name": "To be deleted", "price": 10.0}).encode("utf-8")
        req_post = Request(
            f"{self.base_url}/api/items",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener.open(req_post) as res_post:
            created_id = json.loads(res_post.read().decode())["id"]

        # Delete it
        req_del = Request(f"{self.base_url}/api/items/{created_id}", method="DELETE")
        with self.opener.open(req_del) as res_del:
            self.assertEqual(res_del.status, HTTPStatus.OK)

        # Verify it's gone
        with self.assertRaises(HTTPError) as ctx:
            self.opener.open(f"{self.base_url}/api/items/{created_id}")
        self.assertEqual(ctx.exception.code, HTTPStatus.NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
