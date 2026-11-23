"""Data models for Service B, matching the OpenAPI contract."""
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class Item:
    """Represents an Item data object according to the API contract."""

    id: int
    name: str
    price: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert Item to dictionary for JSON serialization."""
        return asdict(self)
