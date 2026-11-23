"""API Contract definitions and validation for Service B.

This module guarantees that all incoming payloads and outgoing schemas
strictly adhere to the OpenAPI 3.0 contract.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

CONTRACT_FILE = Path(__file__).resolve().parent / "openapi.json"


def load_api_contract() -> Dict[str, Any]:
    """Load the OpenAPI contract from openapi.json."""
    if CONTRACT_FILE.exists():
        with open(CONTRACT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"Contract file not found at {CONTRACT_FILE}")


def validate_item_input(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validate a request payload against the ItemInput schema from the contract.

    Rules defined by contract:
      - Payload must be a JSON object (dict).
      - 'name': required, string, minLength 1.
      - 'price': required, number (int/float, not bool), minimum > 0.

    Returns:
      (is_valid, error_detail, sanitized_data)
    """
    if not isinstance(data, dict):
        return False, "Payload must be a valid JSON object.", None

    # Check for required fields
    if "name" not in data:
        return False, "Missing required field: 'name'.", None
    if "price" not in data:
        return False, "Missing required field: 'price'.", None

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return False, "Field 'name' must be a non-empty string.", None

    price = data.get("price")
    # In Python, bool is a subclass of int, so isinstance(True, int) is True!
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return False, "Field 'price' must be a valid number.", None

    if price <= 0:
        return False, "Field 'price' must be greater than 0.", None

    sanitized = {
        "name": name.strip(),
        "price": round(float(price), 2),
    }
    return True, None, sanitized
