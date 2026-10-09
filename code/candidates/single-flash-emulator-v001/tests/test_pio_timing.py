import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pio_timing import mode0_first_bit_margin_cycles


class PioTimingTests(unittest.TestCase):
    """Check the arithmetic and reject invalid timing assumptions."""

    def test_400_mhz_pio_at_25_mhz_spi_has_one_estimated_cycle(self):
        self.assertEqual(
            mode0_first_bit_margin_cycles(400_000_000, 25_000_000),
            Fraction(1),
        )

    def test_400_mhz_pio_at_50_mhz_spi_misses_estimated_deadline(self):
        self.assertEqual(
            mode0_first_bit_margin_cycles(400_000_000, 50_000_000),
            Fraction(-3),
        )

    def test_150_mhz_pio_at_50_mhz_spi_misses_estimated_deadline(self):
        self.assertEqual(
            mode0_first_bit_margin_cycles(150_000_000, 50_000_000),
            Fraction(-11, 2),
        )

    def test_rejects_non_positive_frequencies(self):
        for pio_hz, spi_hz in ((0, 1), (1, 0), (-1, 1), (1, -1)):
            with (
                self.subTest(pio_hz=pio_hz, spi_hz=spi_hz),
                self.assertRaises(ValueError),
            ):
                mode0_first_bit_margin_cycles(pio_hz, spi_hz)

    def test_rejects_negative_assumed_edge_delay(self):
        with self.assertRaises(ValueError):
            mode0_first_bit_margin_cycles(
                400_000_000,
                25_000_000,
                assumed_edge_to_wait_cycles=-1,
            )


if __name__ == "__main__":
    unittest.main()
