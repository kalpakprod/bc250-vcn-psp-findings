"""Shutdown tests never call real systemctl and refuse the current non-BC host."""

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "shutdown_helper", ROOT / "scripts/waveshare_shutdown.py"
)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class TestShutdown(unittest.TestCase):
    def test_wrong_board_never_calls_executor(self):
        calls = []
        r = helper.shutdown(
            True, identity=lambda: False, executor=lambda cmd: calls.append(cmd)
        )
        self.assertEqual(r["action"], "blocked")
        self.assertEqual(calls, [])

    def test_dry_run_never_calls_executor(self):
        calls = []
        r = helper.shutdown(
            False, identity=lambda: True, executor=lambda cmd: calls.append(cmd)
        )
        self.assertEqual(r["action"], "dry_run")
        self.assertEqual(calls, [])

    def test_exact_fixed_command_after_confirmation(self):
        calls = []

        def executor(cmd):
            calls.append(cmd)
            return 0

        r = helper.shutdown(True, identity=lambda: True, executor=executor)
        self.assertEqual(calls, [["systemctl", "poweroff"]])
        self.assertEqual(r["action"], "shutdown_requested")
        self.assertFalse(r["power_removed_verified"])

    def test_failed_command_not_success(self):
        r = helper.shutdown(True, identity=lambda: True, executor=lambda cmd: 1)
        self.assertEqual(r["action"], "failed")


if __name__ == "__main__":
    unittest.main()
