import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from image_pack import SparseImage, pack_image
from spi_model import ReadRule, SpiNorModel, SpiProtocolError
from toctou_plan import PlannedWindow, TOCTOUPlan


class SpiModelTests(unittest.TestCase):
    """Exercise command parsing and synthetic image selection."""

    def setUp(self):
        self.page = 256
        self.stock = SparseImage(pack_image(b"\x11" * (4 * self.page), self.page))
        self.candidate = SparseImage(pack_image(b"\x22" * (4 * self.page), self.page))

    def test_reads_bytes_from_default_image(self):
        model = SpiNorModel({"stock": self.stock}, "stock")

        self.assertEqual(model.transact(b"\x03\x00\x01\x02", 3), b"\x11" * 3)

    def test_rule_selects_image_for_matching_read_and_address(self):
        model = SpiNorModel(
            {"stock": self.stock, "candidate": self.candidate},
            "candidate",
            rules=(ReadRule(0x100, 0x200, 0, "stock"),),
        )

        result = model.transact(b"\x03\x00\x00\xf0", 0x30)
        self.assertEqual(result[:0x10], b"\x22" * 0x10)
        self.assertEqual(result[0x10:], b"\x11" * 0x20)

    def test_rule_does_not_apply_to_other_read_index(self):
        model = SpiNorModel(
            {"stock": self.stock, "candidate": self.candidate},
            "candidate",
            rules=(ReadRule(0, self.page, 1, "stock"),),
        )

        self.assertEqual(model.transact(b"\x03\x00\x00\x00", 1), b"\x22")
        self.assertEqual(model.transact(b"\x03\x00\x00\x00", 1), b"\x11")

    def test_read_resumes_default_image_after_rule_window(self):
        model = SpiNorModel(
            {"stock": self.stock, "candidate": self.candidate},
            "candidate",
            rules=(ReadRule(0x100, 0x200, 0, "stock"),),
        )

        result = model.transact(b"\x03\x00\x00\xf0", 0x120)
        self.assertEqual(result[:0x10], b"\x22" * 0x10)
        self.assertEqual(result[0x10:0x110], b"\x11" * 0x100)
        self.assertEqual(result[0x110:], b"\x22" * 0x10)

    def test_rejects_unsupported_or_malformed_commands(self):
        model = SpiNorModel({"stock": self.stock}, "stock")

        with self.assertRaises(SpiProtocolError):
            model.transact(b"\x9f\x00\x00\x00", 3)
        with self.assertRaises(SpiProtocolError):
            model.transact(b"\x03\x00\x00", 3)
        with self.assertRaises(SpiProtocolError):
            model.transact(b"\x03\x00\x03\xff", 2)

    def test_rejects_overlapping_rules(self):
        with self.assertRaises(ValueError):
            SpiNorModel(
                {"stock": self.stock, "candidate": self.candidate},
                "candidate",
                rules=(
                    ReadRule(0, 0x100, 0, "stock"),
                    ReadRule(0x80, 0x180, 0, "candidate"),
                ),
            )

    def test_explicit_toctou_plan_pins_hashes_and_order(self):
        plan = TOCTOUPlan.from_images(
            self.stock,
            self.candidate,
            windows=(PlannedWindow(0, 0, self.page, "stock"),),
        )
        model = plan.model({"stock": self.stock, "candidate": self.candidate})
        self.assertEqual(model.transact(b"\x03\x00\x00\x00", 1), b"\x11")
        self.assertEqual(model.transact(b"\x03\x00\x00\x00", 1), b"\x22")
        self.assertEqual(plan.to_json()["hardware"]["flash_authorized"], False)

    def test_toctou_plan_rejects_wrong_image_bytes(self):
        plan = TOCTOUPlan.from_images(
            self.stock,
            self.candidate,
            windows=(PlannedWindow(0, 0, self.page, "stock"),),
        )
        wrong = SparseImage(pack_image(b"\x33" * (4 * self.page), self.page))
        with self.assertRaises(ValueError):
            plan.model({"stock": wrong, "candidate": self.candidate})

    def test_toctou_plan_requires_explicit_nonoverlap(self):
        with self.assertRaises(ValueError):
            TOCTOUPlan.from_images(
                self.stock,
                self.candidate,
                windows=(
                    PlannedWindow(0, 0, self.page, "stock"),
                    PlannedWindow(0, self.page // 2, self.page * 2, "candidate"),
                ),
            )

    def test_zero_length_read_is_valid_and_does_not_change_data(self):
        model = SpiNorModel({"stock": self.stock}, "stock")

        self.assertEqual(model.transact(b"\x03\x00\x00\x00", 0), b"")
        self.assertEqual(model.transact(b"\x03\x00\x00\x00", 1), b"\x11")


if __name__ == "__main__":
    unittest.main()
