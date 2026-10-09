"""Static association/limits, not a claim of actual WiFi/device behavior."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestPanel(unittest.TestCase):
    def test_exact_header_matches_html_and_tcp_window(self):
        html = (
            (ROOT / "candidates/waveshare-adapter-safe-v001/src/network_panel.html")
            .read_text()
            .rstrip("\n")
        )
        header = (
            ROOT / "candidates/waveshare-adapter-safe-v001/src/network_panel.h"
        ).read_text()
        literal = header.split("#define ADAPTER_PANEL_HTML ", 1)[1].strip()
        self.assertEqual(json.loads(literal), html)
        self.assertLessEqual(len(html.encode()) + 257, 2920)

    def test_fan_rpm_display_and_units(self):
        html = (
            ROOT / "candidates/waveshare-adapter-safe-v001/src/network_panel.html"
        ).read_text()
        for index in (1, 2):
            self.assertIn(f"fan{index}_rpm", html)
            self.assertIn(f"<dd id=f{index}>", html)
        self.assertIn("[id,key,scale]", html)
        self.assertIn("m[key]/scale", html)
        self.assertIn("['f1','fan1_rpm',1]", html)
        self.assertIn("['f2','fan2_rpm',1]", html)

    def test_readonly_fixed_endpoint_no_storage_or_external_assets(self):
        html = (
            ROOT / "candidates/waveshare-adapter-safe-v001/src/network_panel.html"
        ).read_text()
        self.assertIn("fetch('/api/status'", html)
        self.assertNotIn("localStorage", html)
        self.assertNotIn("sessionStorage", html)
        self.assertNotRegex(html, r'(?:src|href)=["\']https?://')
        self.assertIn(
            "for(const id of ['bt','os','cpu','gpu','w','f1','f2','u'])", html
        )
        self.assertIn("data:image/svg+xml", html)


if __name__ == "__main__":
    unittest.main()
