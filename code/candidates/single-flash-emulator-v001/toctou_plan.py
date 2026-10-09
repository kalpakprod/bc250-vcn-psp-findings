"""Explicit offline PSP/TOCTOU read-selection plans.

This module is deliberately host-only.  A plan names the two exact image
hashes, the read order, and the address windows to serve.  It never infers a
sequence from filenames and never touches a board or a flash device.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from spi_model import ReadRule, SpiNorModel
from image_pack import SparseImage

@dataclass(frozen=True)
class ImageIdentity:
    name: str
    sha256: str

@dataclass(frozen=True)
class PlannedWindow:
    read_index: int
    start: int
    end: int
    image: str

@dataclass(frozen=True)
class TOCTOUPlan:
    """A fully explicit, bounded image-selection plan."""

    stock: ImageIdentity
    candidate: ImageIdentity
    default_image: str
    windows: tuple[PlannedWindow, ...]
    capacity: int

    def __post_init__(self) -> None:
        if self.default_image not in {self.stock.name, self.candidate.name}:
            raise ValueError("default image must be stock or candidate")
        if self.stock.name == self.candidate.name:
            raise ValueError("stock and candidate names must differ")
        if len(self.stock.sha256) != 64 or len(self.candidate.sha256) != 64:
            raise ValueError("image hashes must be SHA-256 hex strings")
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        for window in self.windows:
            if window.read_index < 0 or window.start < 0:
                raise ValueError("window indexes and starts must be non-negative")
            if window.end <= window.start or window.end > self.capacity:
                raise ValueError("window is outside image capacity")
            if window.image not in {self.stock.name, self.candidate.name}:
                raise ValueError("window names an unknown image")
        for index, window in enumerate(self.windows):
            for other in self.windows[index + 1 :]:
                if (
                    window.read_index == other.read_index
                    and window.start < other.end
                    and other.start < window.end
                ):
                    raise ValueError("windows overlap within one read")

    @classmethod
    def from_images(
        cls,
        stock: SparseImage,
        candidate: SparseImage,
        stock_name: str = "stock",
        candidate_name: str = "candidate",
        default_image: str = "candidate",
        windows: tuple[PlannedWindow, ...] = (),
    ) -> "TOCTOUPlan":
        if stock.image_size != candidate.image_size:
            raise ValueError("stock and candidate capacities differ")
        return cls(
            ImageIdentity(stock_name, hashlib.sha256(stock.unpack()).hexdigest()),
            ImageIdentity(candidate_name, hashlib.sha256(candidate.unpack()).hexdigest()),
            default_image,
            windows,
            stock.image_size,
        )

    def verify_images(self, images: dict[str, SparseImage]) -> None:
        """Reject a plan unless both named images match its pinned hashes."""
        for identity in (self.stock, self.candidate):
            image = images.get(identity.name)
            if image is None:
                raise ValueError(f"missing image: {identity.name}")
            actual = hashlib.sha256(image.unpack()).hexdigest()
            if actual != identity.sha256:
                raise ValueError(f"image hash mismatch: {identity.name}")
            if image.image_size != self.capacity:
                raise ValueError(f"image capacity mismatch: {identity.name}")

    def model(self, images: dict[str, SparseImage]) -> SpiNorModel:
        self.verify_images(images)
        rules = tuple(
            ReadRule(window.start, window.end, window.read_index, window.image)
            for window in self.windows
        )
        return SpiNorModel(images, self.default_image, rules)

    def to_json(self) -> dict:
        return {
            "schema": 1,
            "stock": self.stock.__dict__,
            "candidate": self.candidate.__dict__,
            "default_image": self.default_image,
            "capacity": self.capacity,
            "windows": [window.__dict__ for window in self.windows],
            "hardware": {
                "connected": False,
                "tested": False,
                "flash_authorized": False,
            },
        }

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_json(), indent=2) + "\n")
