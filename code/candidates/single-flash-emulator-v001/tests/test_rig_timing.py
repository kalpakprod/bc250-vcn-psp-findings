"""First-bit deadline from actual responder code, not the older selector."""
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rig_timing import SOURCE, first_bit_margin, first_output_path

class RigTimingTests(unittest.TestCase):
    def test_current_matched_path_misses_25_and_50_mhz_first_sample(self):
        # Manually counted final WAIT -> JMP -> MOV -> JMP -> IRQ -> MOV ->
        # PULL -> NOP -> SET -> WAIT -> OUT: ten cycles before OUT, even with
        # FIFO ready and instant GPIO input synchronization.
        self.assertEqual(len(first_output_path(SOURCE.read_text())) - 1, 10)
        self.assertEqual(first_bit_margin(400_000_000, 25_000_000), Fraction(-2))
        self.assertEqual(first_bit_margin(400_000_000, 50_000_000), Fraction(-6))
        self.assertEqual(first_bit_margin(400_000_000, 20_000_000), Fraction(0))

    def test_changed_instruction_delay_is_not_silently_ignored(self):
        original = SOURCE.read_text()
        self.assertIn("irq nowait 0", original)
        changed = original.replace("irq nowait 0", "irq nowait 0 [1]")
        with self.assertRaises(ValueError):
            first_output_path(changed)

if __name__ == "__main__":
    unittest.main()
