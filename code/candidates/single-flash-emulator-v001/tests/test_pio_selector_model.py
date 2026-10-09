import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pio_selector_model import (
    ReadTransaction,
    SelectorFilter,
    trace_selector_queue,
)


class PioSelectorModelTests(unittest.TestCase):
    """Check source-derived selector timing between synthetic transactions."""

    def test_duplicate_start_filter_and_end_filter_sequence(self):
        start = 0x9DB560
        end = 0x9DB6A0
        steps = trace_selector_queue(
            filters=(
                SelectorFilter(start, True),
                SelectorFilter(start, True),
                SelectorFilter(end, False),
            ),
            transactions=(
                ReadTransaction(0x03, start),
                ReadTransaction(0x03, start),
                ReadTransaction(0x03, 0x1000),
                ReadTransaction(0x03, end),
                ReadTransaction(0x03, 0x1000),
            ),
        )

        self.assertEqual(
            [step.path for step in steps],
            ["pass-through", "inject", "inject", "inject", "pass-through"],
        )
        self.assertEqual(
            [step.selector_at_cs for step in steps],
            [False, True, True, True, False],
        )
        self.assertEqual(
            [step.matched_filter for step in steps],
            [
                SelectorFilter(start, True),
                SelectorFilter(start, True),
                None,
                SelectorFilter(end, False),
                None,
            ],
        )

    def test_only_exact_read_start_consumes_filter(self):
        target = 0x123456
        steps = trace_selector_queue(
            filters=(SelectorFilter(target, True),),
            transactions=(
                ReadTransaction(0x03, target - 1),
                ReadTransaction(0x02, target),
                ReadTransaction(0x03, target),
            ),
        )

        self.assertEqual(
            [step.matched_filter for step in steps],
            [None, None, SelectorFilter(target, True)],
        )
        self.assertEqual([step.selector_at_cs for step in steps], [False, False, False])
        self.assertEqual(
            [step.selector_after_header for step in steps], [False, False, True]
        )


if __name__ == "__main__":
    unittest.main()
