"""Lossless, page-sparse container for a 16 MiB SPI image."""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path

MAGIC = b"B250SPM1"
VERSION = 1
DEFAULT_PAGE_SIZE = 4096
EXPECTED_IMAGE_SIZE = 16 * 1024 * 1024
ERASED_PAGE = 0xFFFFFFFF
HEADER = struct.Struct("<8sHHIIII32s4x")


class ImageFormatError(ValueError):
    """The packed image is malformed or inconsistent."""


def pack_image(image: bytes, page_size: int = DEFAULT_PAGE_SIZE) -> bytes:
    """Build a sparse container without modifying the input image."""
    if page_size <= 0 or page_size & (page_size - 1):
        raise ValueError("page_size must be a positive power of two")
    if not image or len(image) % page_size:
        raise ValueError("image size must be a non-zero multiple of page_size")

    page_count = len(image) // page_size
    page_map: list[int] = []
    payload: list[bytes] = []
    for page_number in range(page_count):
        start = page_number * page_size
        page = image[start : start + page_size]
        if page == b"\xff" * page_size:
            page_map.append(ERASED_PAGE)
        else:
            page_map.append(len(payload))
            payload.append(page)

    header = HEADER.pack(
        MAGIC,
        VERSION,
        page_size,
        len(image),
        page_count,
        len(payload),
        len(payload) * page_size,
        hashlib.sha256(image).digest(),
    )
    mapping = struct.pack(f"<{page_count}I", *page_map)
    return header + mapping + b"".join(payload)


class SparseImage:
    """Validated random-access view of a packed flash image."""

    def __init__(self, packed: bytes):
        if len(packed) < HEADER.size:
            raise ImageFormatError("truncated header")

        (
            magic,
            version,
            self.page_size,
            self.image_size,
            self.page_count,
            payload_pages,
            payload_size,
            self.image_sha256,
        ) = HEADER.unpack_from(packed)
        if magic != MAGIC:
            raise ImageFormatError("bad magic")
        if version != VERSION:
            raise ImageFormatError(f"unsupported version: {version}")
        if self.page_size <= 0 or self.page_size & (self.page_size - 1):
            raise ImageFormatError("invalid page size")
        if self.image_size == 0 or self.image_size % self.page_size:
            raise ImageFormatError("invalid image size")
        if self.page_count != self.image_size // self.page_size:
            raise ImageFormatError("page count does not match image size")
        if payload_size != payload_pages * self.page_size:
            raise ImageFormatError("payload size does not match payload page count")

        map_start = HEADER.size
        map_end = map_start + self.page_count * 4
        payload_end = map_end + payload_size
        if payload_end != len(packed):
            raise ImageFormatError("truncated payload or trailing data")

        self.page_map = struct.unpack_from(f"<{self.page_count}I", packed, map_start)
        used = [page for page in self.page_map if page != ERASED_PAGE]
        if len(used) != payload_pages or sorted(used) != list(range(payload_pages)):
            raise ImageFormatError("page map is duplicated or incomplete")

        self._payload = memoryview(packed)[map_end:payload_end]

    def read(self, address: int, length: int) -> bytes:
        if address < 0 or length < 0 or address + length > self.image_size:
            raise ValueError("read is outside the image")
        result = bytearray()
        while length:
            page_number, page_offset = divmod(address, self.page_size)
            count = min(length, self.page_size - page_offset)
            payload_page = self.page_map[page_number]
            if payload_page == ERASED_PAGE:
                result.extend(b"\xff" * count)
            else:
                start = payload_page * self.page_size + page_offset
                result.extend(self._payload[start : start + count])
            address += count
            length -= count
        return bytes(result)

    def unpack(self) -> bytes:
        image = bytearray(b"\xff" * self.image_size)
        for page_number, payload_page in enumerate(self.page_map):
            if payload_page == ERASED_PAGE:
                continue
            dst = page_number * self.page_size
            src = payload_page * self.page_size
            image[dst : dst + self.page_size] = self._payload[
                src : src + self.page_size
            ]
        return bytes(image)

    def verify_image_hash(self) -> bool:
        return hashlib.sha256(self.unpack()).digest() == self.image_sha256


def _pack_file(source: Path, destination: Path) -> None:
    image = source.read_bytes()
    if len(image) != EXPECTED_IMAGE_SIZE:
        raise ValueError(f"expected a 16 MiB image, got {len(image)} bytes")
    with destination.open("xb") as packed_file:
        packed_file.write(pack_image(image))


def _verify_files(source: Path, packed_path: Path) -> None:
    sparse = SparseImage(packed_path.read_bytes())
    if sparse.image_size != EXPECTED_IMAGE_SIZE:
        raise ImageFormatError("container is not a 16 MiB image")
    image = source.read_bytes()
    actual_hash = hashlib.sha256(image).digest()
    if actual_hash != sparse.image_sha256:
        raise ImageFormatError("container source hash does not match input")
    if sparse.unpack() != image:
        raise ImageFormatError("unpacked bytes differ from input")


def main(argv: list[str] | None = None) -> int:
    """Run the pack or verify command-line operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    pack_parser = subparsers.add_parser("pack", help="pack a 16 MiB image")
    pack_parser.add_argument("source", type=Path)
    pack_parser.add_argument("destination", type=Path)
    verify_parser = subparsers.add_parser("verify", help="verify a packed image")
    verify_parser.add_argument("source", type=Path)
    verify_parser.add_argument("packed", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.command == "pack":
            _pack_file(args.source, args.destination)
            print(
                f"packed {args.source.stat().st_size} bytes into {args.destination.stat().st_size}"
            )
        else:
            _verify_files(args.source, args.packed)
            print("PASS: packed image reconstructs byte-for-byte")
    except (OSError, ValueError, ImageFormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
