"""Actual override-tail diagnostics; known unsafe aborts must remain blocked."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rig_override_model import OverrideTrace

class OverrideTests(unittest.TestCase):
    def test_complete_payload_releases_do_before_hold_and_is_one_shot(self):
        trace = OverrideTrace(b"\xa5")
        trace.levels(cs=0, clk=0)
        for _ in range(8):
            trace.levels(cs=0, clk=1)
            trace.levels(cs=0, clk=0)
        trace.levels(cs=1, clk=0)
        self.assertEqual(trace.sent, [1, 0, 1, 0, 0, 1, 0, 1])
        self.assertTrue(trace.finished)
        self.assertEqual((trace.driving, trace.hold), (False, 1))
        self.assertIn((False, 0), trace.outputs[trace.outputs.index((True, 0)):])
        for clk in (0, 1, 0, 1):
            trace.levels(cs=0, clk=clk)
        self.assertEqual(len(trace.sent), 8)

    def test_early_cs_and_stalled_clk_expose_unsafe_hold_without_recovery(self):
        for cs in (0, 1):
            with self.subTest(cs=cs):
                trace = OverrideTrace(b"\xa5")
                trace.levels(cs=0, clk=0)
                for _ in range(10):
                    trace.levels(cs=cs, clk=0)
                # This is a reproduced blocker, NOT an assertion of safety.
                self.assertEqual((trace.driving, trace.hold), (True, 0))
                self.assertFalse(trace.finished)
                self.assertEqual(len(trace.sent), 1)

if __name__ == "__main__":
    unittest.main()
