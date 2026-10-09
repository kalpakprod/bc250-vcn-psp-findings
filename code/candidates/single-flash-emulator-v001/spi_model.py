"""Host-side model for the explicitly implemented SPI read command."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from image_pack import SparseImage

READ_DATA = 0x03


class SpiProtocolError(ValueError):
    """The synthetic SPI transaction is outside the implemented protocol."""


@dataclass(frozen=True)
class ReadRule:
    """Select an image for an address range on one transaction index."""

    start: int
    end: int
    read_index: int
    image: str


class SpiNorModel:
    """Model 0x03 reads, with optional per-read address-window selection."""

    def __init__(
        self,
        images: Mapping[str, SparseImage],
        default_image: str,
        rules: tuple[ReadRule, ...] = (),
    ):
        if not images or default_image not in images:
            raise ValueError("default_image must name a supplied image")
        image_sizes = {image.image_size for image in images.values()}
        if len(image_sizes) != 1:
            raise ValueError("all images must have the same capacity")
        self.images = dict(images)
        self.default_image = default_image
        self.capacity = next(iter(image_sizes))
        self.rules = rules
        self.read_index = 0

        for index, rule in enumerate(rules):
            if rule.image not in self.images:
                raise ValueError(f"rule names unknown image: {rule.image}")
            if rule.start < 0 or rule.end <= rule.start or rule.end > self.capacity:
                raise ValueError("rule range is outside image capacity")
            if rule.read_index < 0:
                raise ValueError("read_index must be non-negative")
            for other in rules[index + 1 :]:
                if (
                    rule.read_index == other.read_index
                    and rule.start < other.end
                    and other.start < rule.end
                ):
                    raise ValueError("rules for one read index must not overlap")

    def _selection(self, address: int, read_index: int) -> tuple[SparseImage, int]:
        for rule in self.rules:
            if rule.read_index == read_index and rule.start <= address < rule.end:
                return self.images[rule.image], rule.end
        next_start = min(
            (
                rule.start
                for rule in self.rules
                if rule.read_index == read_index and rule.start > address
            ),
            default=self.capacity,
        )
        return self.images[self.default_image], next_start

    def transact(self, header: bytes, response_length: int) -> bytes:
        if len(header) != 4:
            raise SpiProtocolError("expected one opcode byte and three address bytes")
        if header[0] != READ_DATA:
            raise SpiProtocolError(f"unsupported opcode 0x{header[0]:02x}")
        if response_length < 0:
            raise SpiProtocolError("response length must be non-negative")

        address = int.from_bytes(header[1:4], "big")
        if address > self.capacity or response_length > self.capacity - address:
            raise SpiProtocolError("read extends beyond image capacity")

        current_read = self.read_index
        self.read_index += 1
        result = bytearray()
        while response_length:
            image, segment_end = self._selection(address, current_read)
            count = min(response_length, segment_end - address)
            result.extend(image.read(address, count))
            address += count
            response_length -= count
        return bytes(result)
