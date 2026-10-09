"""Host-only fixture checks; no real procfs/sysfs or hardware access."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "clock_probe",
    Path(__file__).resolve().parents[1] / "scripts/probe_bc250_clocks_readonly.py",
)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class ClockProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def card(self, name, vendor="0x1002", device="0x13fe"):
        dev = self.root / name / "device"
        dev.mkdir(parents=True)
        (dev / "vendor").write_text(vendor)
        (dev / "device").write_text(device)
        return dev

    def capture(self):
        original = probe.read_text

        def fixture_read(path):
            return original(path) if path.is_relative_to(self.root) else None

        output = io.StringIO()
        with (
            patch.object(probe, "DRM_ROOT", self.root),
            patch.object(probe, "TARGET_PCI_ID", "0x13fe"),
            patch.object(probe, "read_text", side_effect=fixture_read),
            patch.object(probe.platform, "node", return_value="fixture"),
            patch.object(probe.platform, "platform", return_value="fixture-os"),
            patch.object(probe.platform, "release", return_value="fixture-kernel"),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(probe.main(), 0)
        return json.loads(output.getvalue())

    def test_empty_tree_is_not_hardware_evidence(self):
        data = self.capture()
        self.assertEqual(data["cards"], [])
        self.assertFalse(data["hardware_mutation"])

    def test_exact_target_filter(self):
        self.card("card0", device="0x1900")
        self.card("card1", vendor="0x8086")
        self.card("card2")
        data = self.capture()
        self.assertEqual([c["card"] for c in data["cards"]], ["card2"])
        self.assertEqual(data["skipped_cards"][0]["device"], "0x1900")

    def test_metrics_hash_and_alias_uncertainty(self):
        dev = self.card("card0")
        raw = b"\x00\x01\x02\xff"
        (dev / "gpu_metrics").write_bytes(raw)
        for name in ("pp_dpm_mclk", "pp_dpm_fclk"):
            (dev / name).write_text("0: 1420Mhz *\n")
        card = self.capture()["cards"][0]
        self.assertEqual(card["independent_sources_checked"], "unknown")
        blob = card["files"]["gpu_metrics"]
        self.assertEqual(bytes.fromhex(blob["hex"]), raw)
        self.assertEqual(blob["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(blob["size"], len(raw))

    def test_missing_files_are_optional(self):
        self.card("card0")
        self.assertEqual(self.capture()["cards"][0]["files"], {})

    def test_fixture_files_unchanged(self):
        dev = self.card("card0")
        (dev / "pp_dpm_mclk").write_text("0: 1420Mhz *\n")
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.capture()
        after = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
