"""Service layer defining the interface and its implementation."""
from abc import ABC, abstractmethod
from typing import List, Optional
from models import Item


class ItemServiceInterface(ABC):
    """Interface (contract) for item data management.

    Decouples business and data operations from HTTP transport.
    """

    @abstractmethod
    def get_all(self) -> List[Item]:
        """Retrieve all items."""
        pass

    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[Item]:
        """Retrieve a single item by its ID. Returns None if not found."""
        pass

    @abstractmethod
    def create(self, name: str, price: float) -> Item:
        """Create a new item and return the created entity."""
        pass

    @abstractmethod
    def update(self, item_id: int, name: str, price: float) -> Optional[Item]:
        """Update an existing item. Returns None if item does not exist."""
        pass

    @abstractmethod
    def delete(self, item_id: int) -> bool:
        """Delete an item by ID. Returns True if deleted, False if not found."""
        pass


class InMemoryItemService(ItemServiceInterface):
    """In-memory implementation of the ItemServiceInterface."""

    def __init__(self, initial_items: Optional[List[Item]] = None):
        self._items = {}
        if initial_items:
            for item in initial_items:
                self._items[item.id] = item
            self._next_id = max(self._items.keys(), default=0) + 1
        else:
            self._next_id = 1

    def get_all(self) -> List[Item]:
        return list(self._items.values())

    def get_by_id(self, item_id: int) -> Optional[Item]:
        return self._items.get(item_id)

    def create(self, name: str, price: float) -> Item:
        item = Item(id=self._next_id, name=name, price=round(float(price), 2))
        self._items[self._next_id] = item
        self._next_id += 1
        return item

    def update(self, item_id: int, name: str, price: float) -> Optional[Item]:
        if item_id not in self._items:
            return None
        updated = Item(id=item_id, name=name, price=round(float(price), 2))
        self._items[item_id] = updated
        return updated

    def delete(self, item_id: int) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False
