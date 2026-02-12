"""KS SnapClip in-memory capture store for recent screenshots."""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from PIL import Image
import os


@dataclass
class CaptureItem:
    image: Image.Image
    timestamp: datetime
    name: Optional[str] = None


class CaptureStore:
    def __init__(self, max_items: int = 20):
        self.max_items = max_items
        self._items: List[CaptureItem] = []

    def add(self, image: Image.Image, name: Optional[str] = None):
        item = CaptureItem(image=image, timestamp=datetime.now(), name=name)
        self._items.insert(0, item)
        # trim
        self._items = self._items[: self.max_items]
        return item

    def recent(self, limit: Optional[int] = None):
        if limit is None:
            return list(self._items)
        return list(self._items)[:limit]

    def save(self, index: int, folder: str, prefix: str = "screenshot") -> str:
        """Save the capture at `index` to `folder` and return the file path."""
        if index < 0 or index >= len(self._items):
            raise IndexError("Capture index out of range")
        os.makedirs(folder, exist_ok=True)
        item = self._items[index]
        ts = item.timestamp.strftime("%Y%m%d_%H%M%S")
        fname = f"{prefix}_{ts}.png"
        path = os.path.join(folder, fname)
        item.image.save(path)
        return path
