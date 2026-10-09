import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from image_pack import ImageFormatError, SparseImage, pack_image


class ImagePackTests(unittest.TestCase):
    """Exercise sparse image packing, reading, and validation."""

    page_size = 256

    def test_round_trip_with_erased_and_populated_pages(self):
        source = (
            b"\xff" * self.page_size
            + bytes(range(256))
            + b"\xff" * self.page_size
            + bytes(reversed(range(256)))
        )
        packed = pack_image(source, self.page_size)
        sparse = SparseImage(packed)

        self.assertEqual(sparse.unpack(), source)
        self.assertTrue(sparse.verify_image_hash())
        self.assertEqual(sparse.read(0, len(source)), source)

    def test_read_crossing_page_boundary(self):
        source = bytes(range(256)) + bytes(reversed(range(256)))
        sparse = SparseImage(pack_image(source, self.page_size))

        self.assertEqual(sparse.read(250, 20), source[250:270])

    def test_all_erased_image_has_no_payload(self):
        source = b"\xff" * (3 * self.page_size)
        sparse = SparseImage(pack_image(source, self.page_size))

        self.assertEqual(sparse.unpack(), source)
        self.assertEqual(sparse.read(0, len(source)), source)
        self.assertEqual(len(sparse._payload), 0)

    def test_rejects_reads_outside_image(self):
        sparse = SparseImage(pack_image(b"\x00" * self.page_size, self.page_size))

        with self.assertRaises(ValueError):
            sparse.read(-1, 1)
        with self.assertRaises(ValueError):
            sparse.read(self.page_size, 1)

    def test_rejects_truncated_and_trailing_data(self):
        packed = pack_image(b"\x00" * self.page_size, self.page_size)

        with self.assertRaises(ImageFormatError):
            SparseImage(packed[:-1])
        with self.assertRaises(ImageFormatError):
            SparseImage(packed + b"\x00")

    def test_rejects_duplicate_page_map_entries(self):
        source = b"\x00" * self.page_size + b"\x01" * self.page_size
        packed = bytearray(pack_image(source, self.page_size))
        map_start = 64
        packed[map_start + 4 : map_start + 8] = packed[map_start : map_start + 4]

        with self.assertRaises(ImageFormatError):
            SparseImage(bytes(packed))

    def test_container_records_source_hash(self):
        source = b"\xa5" * self.page_size
        sparse = SparseImage(pack_image(source, self.page_size))

        self.assertEqual(sparse.image_sha256, hashlib.sha256(source).digest())


if __name__ == "__main__":
    unittest.main()
