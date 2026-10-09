import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
BUILDER = ROOT / "scripts/build_clv_oc_candidate.py"
PINNED_SHA256 = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"

# S1 H1330 template (ROM offsets), per s1-a brief. 0xBD2 is ASSERT-only
# (never written); 0x83C defaults to 0xFF unless S1-C verdict approves 0x00.
H1330_TARGET = {0x7E5: 0x1A, 0x7FF: 0x01, 0xBD2: 0x01, 0xBD3: 0x32, 0xBD4: 0x05}
H1330_ROM_U16 = 0x0532
H1330_TEMPLATE_OFFSETS = frozenset({0x7E5, 0x7FF, 0xBD3, 0xBD4})
H1330_PROFILE_CANDIDATES = ("h1330", "H1330", "s1-h1330", "S1-H1330")
S1C_VERDICT = ROOT / "candidates/s1-h1330/S1C-verdict.json"

_BUILDER_PROFILES_CACHE = None


def builder_profiles():
    """Return the builder's supported --profile set without side effects."""
    global _BUILDER_PROFILES_CACHE
    if _BUILDER_PROFILES_CACHE is not None:
        return _BUILDER_PROFILES_CACHE
    profiles = set()
    try:
        scripts = str(ROOT / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        spec = importlib.util.spec_from_file_location("clv_oc_builder_probe", BUILDER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        profiles = set(getattr(module, "PROFILES", {}))
    except Exception:
        profiles = set()
    if not profiles:
        try:
            help_text = subprocess.run(
                [sys.executable, str(BUILDER), "--help"], capture_output=True, text=True
            ).stdout
            start, end = help_text.find("{"), help_text.find("}")
            if 0 <= start < end:
                profiles = {
                    p.strip()
                    for p in help_text[start + 1 : end].split(",")
                    if p.strip()
                }
        except Exception:
            profiles = set()
    _BUILDER_PROFILES_CACHE = profiles
    return profiles


def h1330_profile():
    """Return the supported H1330 profile name, or None if builder lacks it."""
    available = builder_profiles()
    for candidate in H1330_PROFILE_CANDIDATES:
        if candidate in available:
            return candidate
    return None


def s1c_approves_00():
    """True only if S1-C verdict file exists and recommends 0x00 for +0x36D."""
    try:
        verdict = json.loads(S1C_VERDICT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return str(verdict.get("recommendation", "")).strip().lower() in (
        "0x00",
        "0x0",
        "00",
    )


# S2 fixed-voltage stage (s2 briefs). S2 builds ONLY on the verified S1 base
# and applies the arbitrated S2-A Setup template plus the S2-B VDD offset
# (which stays 0 unless S2-B closed with a stated value). Template offsets are
# ROM-absolute, matching the S1 convention. Builder-dependent tests skip
# (not fail) until S2-C lands the S2 profile.
S1_BASE = ROOT / "candidates/s1-h1330/BC250_5.00_clv_S1-H1330_v001.bin"
S1_PINNED_SHA256 = "c5dc6424b3d836b0a262ed54d9c3e747f2c33d40cb614fac40e4ea46e7bfbf7c"
S2A_VERDICT = ROOT / "candidates/s2-ocv/S2A-verdict.json"
S2B_VERDICT = ROOT / "candidates/s2-ocv/S2B-verdict.json"
S2_PROVENANCE = ROOT / "candidates/s2-ocv/S2-OCV_v001.provenance.json"
S2_PROFILE_CANDIDATES = ("s2-ocv", "S2-OCV", "s2", "S2", "s2_ocv", "S2_OCV")
S1_PRESERVED = {
    0x7E5: 0x1A,
    0x7FF: 0x01,
    0x83C: 0xFF,
    0xBD2: 0x01,
    0xBD3: 0x32,
    0xBD4: 0x05,
}
VDD_OFFSET_BYTES = (0xBB4, 0xBB5)  # AmdSetup body 0x4CF + 0x6E5/+0x6E6
VDD_OFFSET_WINDOW = (0xBB4, 0xBB8)  # u32 container for a closed S2-B value
SOC_SETPOINT_DENYLIST = ("soc115", "soc-1.15v", "soc_1v15", "s2-soc115")


def s2_profile():
    """Return the supported S2 profile name, or None if builder lacks it."""
    available = builder_profiles()
    for candidate in S2_PROFILE_CANDIDATES:
        if candidate in available:
            return candidate
    return None


def load_verdict(path):
    """Return parsed verdict JSON, or None when missing/unparseable."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def expand_s2a_template(s2a):
    """Expand the S2A template to {rom_offset: (from_or_None, to, entry)}.

    Scalar values wider than one byte expand little-endian from the entry
    offset, so a u16 entry covers offset and offset+1.
    """
    writes = {}
    for entry in s2a.get("template", []):
        offset = entry["offset"]
        offset = int(offset, 16) if isinstance(offset, str) else int(offset)
        raw_from, raw_to = entry.get("from"), entry["to"]
        to_int = int(raw_to, 16) if isinstance(raw_to, str) else int(raw_to)
        if raw_from is None:
            from_int = None
        elif isinstance(raw_from, str):
            from_int = int(raw_from, 16)
        else:
            from_int = int(raw_from)
        width = int(entry.get("width", 0) or 0)
        if not width:
            width = max(1, (max(to_int, from_int or 0).bit_length() + 7) // 8)
        to_blob = to_int.to_bytes(width, "little")
        from_blob = None if from_int is None else from_int.to_bytes(width, "little")
        for i in range(width):
            writes[offset + i] = (
                None if from_blob is None else from_blob[i],
                to_blob[i],
                entry,
            )
    return writes


def arbitrated_changed_set(s1, s2a, s2b):
    """Return (writes, expected_changed) for the S2 verdicts against base s1.

    expected_changed is the exact set of ROM offsets that must differ
    S1-vs-S2: S2A bytes whose target differs from S1, plus VDD offset bytes
    only when S2-B closed with a value.
    """
    writes = expand_s2a_template(s2a)
    expected = {
        offset for offset, (frm, to, entry) in writes.items() if s1[offset] != to
    }
    if s2b.get("closed"):
        expect32 = int(s2b["value_u32"]).to_bytes(4, "little")
        for i in range(4):
            if s1[0xBB4 + i] != expect32[i]:
                expected.add(0xBB4 + i)
    return writes, expected


def vdd_bytes_match_value(image, value):
    """True when the VDD offset bytes encode value_u32 (u16 or u32 LE at 0xBB4)."""
    window = bytes(image[VDD_OFFSET_WINDOW[0] : VDD_OFFSET_WINDOW[1]])
    expect = int(value).to_bytes(4, "little")
    return window == expect or window[:2] == expect[:2]


@unittest.skipUnless(SOURCE.exists(), "local firmware fixture unavailable")
class ClvBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name) / "candidate.bin"

    def run_builder(self, source=SOURCE, *extra):
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(source),
                str(self.output),
                "--profile",
                "df1400",
                *extra,
            ],
            capture_output=True,
            text=True,
        )

    def test_exact_delta_and_source_preserved(self):
        before = SOURCE.read_bytes()
        result = self.run_builder()
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.output.read_bytes()
        self.assertEqual(
            [i for i, (a, b) in enumerate(zip(before, after)) if a != b], [0xBD3]
        )
        self.assertEqual(after[0xBD3:0xBD5], (1400).to_bytes(2, "little"))
        self.assertEqual(
            hashlib.sha256(SOURCE.read_bytes()).digest(),
            hashlib.sha256(before).digest(),
        )

    def test_altered_source_rejected(self):
        data = bytearray(SOURCE.read_bytes())
        data[0x30000] ^= 1
        altered = Path(self.tmp.name) / "altered.bin"
        altered.write_bytes(data)
        self.assertNotEqual(self.run_builder(altered).returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_suffix(".build.json").exists())

    def test_missing_record_and_truncation_rejected(self):
        for data in (
            SOURCE.read_bytes()[:100],
            SOURCE.read_bytes().replace(b"AmdSetup\0", b"BadSetup\0"),
        ):
            altered = Path(self.tmp.name) / "altered.bin"
            altered.write_bytes(data)
            self.assertNotEqual(self.run_builder(altered).returncode, 0)
            self.assertFalse(self.output.exists())

    def test_unsupported_voltage_sync_and_frequency_rejected(self):
        for args in [
            ("--vdd", "80"),
            ("--df-clock", "65535"),
            ("--profile", "sync"),
            ("--profile", "vdd80"),
        ]:
            self.assertNotEqual(self.run_builder(SOURCE, *args).returncode, 0)
            self.assertFalse(self.output.exists())

    def test_existing_manifest_preserved(self):
        manifest = self.output.with_suffix(".build.json")
        manifest.write_text("sentinel")
        self.assertNotEqual(self.run_builder().returncode, 0)
        self.assertEqual(manifest.read_text(), "sentinel")
        self.assertFalse(self.output.exists())

    def test_existing_output_preserved(self):
        self.output.write_bytes(b"sentinel")
        self.assertNotEqual(self.run_builder().returncode, 0)
        self.assertEqual(self.output.read_bytes(), b"sentinel")

    def test_in_place_rejected(self):
        self.output = SOURCE
        self.assertNotEqual(self.run_builder().returncode, 0)


@unittest.skipUnless(SOURCE.exists(), "local firmware fixture unavailable")
class H1330PositiveTests(unittest.TestCase):
    """H1330 template coverage. Skips (not fails) until builder grows H1330."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name) / "candidate-h1330.bin"

    def run_profile(self, profile, source=SOURCE, output=None, *extra):
        target = output or self.output
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(source),
                str(target),
                "--profile",
                profile,
                *extra,
            ],
            capture_output=True,
            text=True,
        )

    def require_h1330(self):
        profile = h1330_profile()
        if profile is None:
            self.skipTest(
                "builder lacks H1330 profile (has %s)" % sorted(builder_profiles())
            )
        return profile

    def test_h1330_template_bytes(self):
        profile = self.require_h1330()
        before = SOURCE.read_bytes()
        result = self.run_profile(profile)
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.output.read_bytes()
        self.assertEqual(len(after), len(before))
        for offset, value in H1330_TARGET.items():
            self.assertEqual(after[offset], value, "ROM %s" % hex(offset))
        self.assertEqual(int.from_bytes(after[0xBD3:0xBD5], "little"), H1330_ROM_U16)
        changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        allowed = set(H1330_TEMPLATE_OFFSETS)
        if s1c_approves_00():
            allowed.add(0x83C)
            self.assertEqual(after[0x83C], 0x00)
        else:
            self.assertEqual(after[0x83C], 0xFF)
            self.assertNotIn(0x83C, changed)
        self.assertNotIn(0xBD2, changed, "0xBD2 is assert-only, never written")
        for offset in [o for o in H1330_TARGET if before[o] != H1330_TARGET[o]]:
            self.assertIn(offset, changed, "expected change at %s" % hex(offset))
        self.assertEqual(
            set(changed) - allowed,
            set(),
            "unexpected changed bytes: %s"
            % [hex(i) for i in changed if i not in allowed],
        )
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), PINNED_SHA256)

    def test_h1330_bd2_asserted_and_preserved(self):
        profile = self.require_h1330()
        result = self.run_profile(profile)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_bytes()[0xBD2], 0x01)
        corrupted = bytearray(SOURCE.read_bytes())
        corrupted[0xBD2] ^= 0xFF
        bad_source = Path(self.tmp.name) / "bd2-corrupt.bin"
        bad_source.write_bytes(corrupted)
        bad_output = Path(self.tmp.name) / "bd2-rejected.bin"
        rejected = self.run_profile(profile, bad_source, bad_output)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(bad_output.exists())
        self.assertFalse(bad_output.with_suffix(".build.json").exists())

    def test_h1330_provenance_schema(self):
        profile = self.require_h1330()
        result = self.run_profile(profile)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = self.output.with_suffix(".build.json")
        self.assertTrue(manifest.exists(), "builder manifest missing")
        report = json.loads(manifest.read_text(encoding="utf-8"))
        for key in (
            "profile",
            "source_sha256",
            "output_sha256",
            "changed_offsets",
            "changed_byte_count",
        ):
            self.assertIn(key, report, "manifest key %s" % key)
        self.assertEqual(report["profile"], profile)
        self.assertEqual(report["source_sha256"], PINNED_SHA256)
        self.assertEqual(
            report["output_sha256"],
            hashlib.sha256(self.output.read_bytes()).hexdigest(),
        )
        changed = [int(x, 16) for x in report["changed_offsets"]]
        actual = [
            i
            for i, (a, b) in enumerate(
                zip(SOURCE.read_bytes(), self.output.read_bytes())
            )
            if a != b
        ]
        self.assertEqual(sorted(changed), sorted(actual))
        self.assertEqual(report["changed_byte_count"], len(actual))
        self.assertIs(report.get("voltage_changed"), False)
        version = report.get("builder_version", report.get("version"))
        if version is not None:
            self.assertTrue(str(version).strip(), "empty builder version")


@unittest.skipUnless(SOURCE.exists(), "local firmware fixture unavailable")
class S1NegativeTests(unittest.TestCase):
    """S1 rejection coverage that must pass with the current builder."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_builder(self, profile_args, source=SOURCE, name="candidate.bin"):
        output = Path(self.tmp.name) / name
        return (
            subprocess.run(
                [sys.executable, str(BUILDER), str(source), str(output), *profile_args],
                capture_output=True,
                text=True,
            ),
            output,
        )

    def test_reject_unknown_profile(self):
        for index, bogus in enumerate(("not-a-real-profile", "df1401")):
            result, output = self.run_builder(
                ["--profile", bogus], name="bogus-%d.bin" % index
            )
            self.assertNotEqual(result.returncode, 0, "profile %s accepted" % bogus)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".build.json").exists())

    def test_reject_voltage_bytes_in_s1(self):
        result, output = self.run_builder(["--profile", "df1400"])
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(
            output.with_suffix(".build.json").read_text(encoding="utf-8")
        )
        self.assertIs(report.get("voltage_changed"), False)
        changed = [int(x, 16) for x in report["changed_offsets"]]
        self.assertEqual(changed, [0xBD3])
        rejected, novolt = self.run_builder(
            ["--profile", "df1400", "--vdd", "80"], name="vdd-rejected.bin"
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(novolt.exists())
        profile = h1330_profile()
        if profile is not None:
            h_result, h_output = self.run_builder(
                ["--profile", profile], name="h1330-novolt.bin"
            )
            self.assertEqual(h_result.returncode, 0, h_result.stderr)
            h_report = json.loads(
                h_output.with_suffix(".build.json").read_text(encoding="utf-8")
            )
            self.assertIs(h_report.get("voltage_changed"), False)
            h_changed = {int(x, 16) for x in h_report["changed_offsets"]}
            self.assertEqual(h_changed - set(H1330_TEMPLATE_OFFSETS) - {0x83C}, set())

    def test_reject_wrong_base_hash(self):
        for index, offset in enumerate((0x7E5, 0xBD3)):
            corrupted = bytearray(SOURCE.read_bytes())
            corrupted[offset] ^= 0x01
            bad_source = Path(self.tmp.name) / ("wrongbase-%d.bin" % index)
            bad_source.write_bytes(corrupted)
            result, output = self.run_builder(
                ["--profile", "df1400"],
                source=bad_source,
                name="wrongbase-%d-out.bin" % index,
            )
            self.assertNotEqual(
                result.returncode, 0, "corrupt %s accepted" % hex(offset)
            )
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".build.json").exists())


class S2PositiveTests(unittest.TestCase):
    """S2 fixed-voltage coverage. Builder tests skip until S2-C lands the profile."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name) / "candidate-s2.bin"

    def require_s1_base(self):
        if not S1_BASE.exists():
            self.skipTest("S1 base image missing: %s" % S1_BASE)
        return S1_BASE.read_bytes()

    def require_s2_profile(self):
        profile = s2_profile()
        if profile is None:
            self.skipTest(
                "builder lacks S2 profile (has %s)" % sorted(builder_profiles())
            )
        return profile

    def require_s2_verdicts(self):
        s2a, s2b = load_verdict(S2A_VERDICT), load_verdict(S2B_VERDICT)
        if s2a is None or s2b is None:
            missing = ", ".join(
                str(p) for p, v in ((S2A_VERDICT, s2a), (S2B_VERDICT, s2b)) if v is None
            )
            self.skipTest("S2 verdict pending: %s" % missing)
        return s2a, s2b

    def run_s2(self, profile, source, output=None):
        target = output or self.output
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(source),
                str(target),
                "--profile",
                profile,
            ],
            capture_output=True,
            text=True,
        )

    def test_s2_s1_base_pinned_and_intact(self):
        """S1-base assertion: S2 builds only on verified S1 v001 with offset 0."""
        s1 = self.require_s1_base()
        self.assertEqual(len(s1), 0x1000000)
        self.assertEqual(hashlib.sha256(s1).hexdigest(), S1_PINNED_SHA256)
        for offset, value in S1_PRESERVED.items():
            self.assertEqual(s1[offset], value, "S1 base ROM %s" % hex(offset))
        self.assertEqual(int.from_bytes(s1[0xBD3:0xBD5], "little"), 0x0532)
        for offset in VDD_OFFSET_BYTES:
            self.assertEqual(
                s1[offset], 0x00, "S1 base VDD offset ROM %s must be 0" % hex(offset)
            )

    def test_s2_template_bytes(self):
        """S2 output is S1 base plus exactly the arbitrated S2-A/S2-B writes."""
        s1 = self.require_s1_base()
        self.assertEqual(
            hashlib.sha256(s1).hexdigest(),
            S1_PINNED_SHA256,
            "S2 requires the verified S1 base",
        )
        profile = self.require_s2_profile()
        s2a, s2b = self.require_s2_verdicts()
        self.assertIsInstance(s2a.get("template"), list, "S2A template must be a list")
        for entry in s2a["template"]:
            self.assertIn("offset", entry)
            self.assertIn("to", entry)
        writes, expected = arbitrated_changed_set(s1, s2a, s2b)
        top_citations = s2a.get("citations", [])
        for offset, (frm, to, entry) in sorted(writes.items()):
            cites = entry.get("citation") or entry.get("citations") or top_citations
            self.assertTrue(cites, "uncited arbitrated write at %s" % hex(offset))
            if frm is not None:
                self.assertEqual(
                    s1[offset],
                    frm,
                    "verdict from-byte mismatch at %s (offsets must be ROM-absolute)"
                    % hex(offset),
                )
        if s2b.get("closed"):
            for key in ("consumer", "rail", "unit"):
                self.assertTrue(
                    str(s2b.get(key) or "").strip(), "closed S2-B lacks %s" % key
                )
            self.assertTrue(s2b.get("citations"), "closed S2-B lacks citations")
            self.assertIsInstance(
                s2b.get("value_u32"), int, "closed S2-B lacks integer value_u32"
            )
        result = self.run_s2(profile, S1_BASE)
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.output.read_bytes()
        self.assertEqual(len(after), len(s1))
        for offset, value in S1_PRESERVED.items():
            if offset not in writes:
                self.assertEqual(
                    after[offset], value, "S1 field clobbered at %s" % hex(offset)
                )
        for offset, (frm, to, entry) in writes.items():
            self.assertEqual(after[offset], to, "arbitrated byte %s" % hex(offset))
        if s2b.get("closed"):
            self.assertTrue(
                vdd_bytes_match_value(after, s2b["value_u32"]),
                "VDD bytes do not encode u32 %r: 0xBB4..0xBB8=%s"
                % (s2b["value_u32"], bytes(after[0xBB4:0xBB8]).hex()),
            )
        else:
            for offset in VDD_OFFSET_BYTES:
                self.assertEqual(
                    after[offset],
                    0x00,
                    "VDD offset written without S2-B closure at %s" % hex(offset),
                )
        changed = {i for i, (a, b) in enumerate(zip(s1, after)) if a != b}
        self.assertEqual(
            changed,
            expected,
            "S2 changed set != arbitrated template: extra=%s missing=%s"
            % (
                sorted(hex(i) for i in changed - expected),
                sorted(hex(i) for i in expected - changed),
            ),
        )
        self.assertEqual(
            hashlib.sha256(S1_BASE.read_bytes()).hexdigest(), S1_PINNED_SHA256
        )

    def test_s2_manifest_schema(self):
        """S2 builder manifest pins the S1 base and reports the exact delta."""
        s1 = self.require_s1_base()
        profile = self.require_s2_profile()
        result = self.run_s2(profile, S1_BASE)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = self.output.with_suffix(".build.json")
        self.assertTrue(manifest.exists(), "S2 builder manifest missing")
        report = json.loads(manifest.read_text(encoding="utf-8"))
        for key in (
            "profile",
            "source_sha256",
            "output_sha256",
            "changed_offsets",
            "changed_byte_count",
        ):
            self.assertIn(key, report, "manifest key %s" % key)
        self.assertEqual(report["profile"], profile)
        self.assertEqual(
            report["source_sha256"],
            S1_PINNED_SHA256,
            "S2 manifest must pin the S1 base hash",
        )
        after = self.output.read_bytes()
        self.assertEqual(report["output_sha256"], hashlib.sha256(after).hexdigest())
        changed = [int(x, 16) for x in report["changed_offsets"]]
        actual = [i for i, (a, b) in enumerate(zip(s1, after)) if a != b]
        self.assertEqual(sorted(changed), sorted(actual))
        self.assertEqual(report["changed_byte_count"], len(actual))
        self.assertIs(report.get("hardware_written"), False)
        blob = json.dumps(report)
        self.assertTrue(
            "REQUEST_ONLY" in blob or "NOT_FLASH_APPROVED" in blob,
            "S2 manifest lacks request-only label",
        )
        version = report.get("builder_version", report.get("version"))
        if version is not None:
            self.assertTrue(str(version).strip(), "empty builder version")
        s2a, s2b = load_verdict(S2A_VERDICT), load_verdict(S2B_VERDICT)
        if s2a is not None and s2b is not None:
            _, expected = arbitrated_changed_set(s1, s2a, s2b)
            self.assertEqual(
                set(changed), expected, "manifest changed set != arbitrated template"
            )

    def test_s2_provenance_file_schema(self):
        """S2-OCV provenance file references S1 base, verdicts, delta, no-flash labels."""
        if not S2_PROVENANCE.exists():
            self.skipTest("S2-C provenance not built yet: %s" % S2_PROVENANCE)
        prov = json.loads(S2_PROVENANCE.read_text(encoding="utf-8"))
        blob = json.dumps(prov)
        self.assertIn(
            S1_PINNED_SHA256, blob, "provenance must reference the S1 base hash"
        )
        self.assertTrue(
            "REQUEST_ONLY" in blob or "NOT_FLASH_APPROVED" in blob,
            "provenance lacks request-only label",
        )
        self.assertIn("S2A-verdict", blob, "provenance must reference the S2-A verdict")
        self.assertIn("S2B-verdict", blob, "provenance must reference the S2-B verdict")
        self.assertTrue(
            "changed_bytes" in prov
            or "changed_offsets" in prov
            or "changed_byte_count" in prov,
            "provenance lacks a changed-bytes record",
        )
        reported = set()
        for entry in prov.get("changed_bytes", []) or []:
            raw = entry.get("offset") if isinstance(entry, dict) else entry
            reported.add(int(raw, 16) if isinstance(raw, str) else int(raw))
        for raw in prov.get("changed_offsets", []) or []:
            reported.add(int(raw, 16) if isinstance(raw, str) else int(raw))
        s2a, s2b = load_verdict(S2A_VERDICT), load_verdict(S2B_VERDICT)
        if s2a is None or s2b is None or not S1_BASE.exists():
            return
        _, expected = arbitrated_changed_set(S1_BASE.read_bytes(), s2a, s2b)
        self.assertEqual(reported, expected, "provenance delta != arbitrated template")
        if not expected:
            lowered = blob.lower()
            self.assertTrue(
                any(
                    tag in lowered
                    for tag in (
                        "no_change",
                        "no-change",
                        "identical",
                        "zero-change",
                        "zero_change",
                        "unchanged",
                    )
                ),
                "no-change S2 provenance must state no-change explicitly",
            )

    def test_s2_no_change_case(self):
        """Explicit no-change path: byte-identical to S1 with a zero-count manifest."""
        s1 = self.require_s1_base()
        s2a, s2b = self.require_s2_verdicts()
        if s2a.get("template") or not s2a.get("no_change", False) or s2b.get("closed"):
            self.skipTest("verdicts specify S2 changes; no-change path not applicable")
        profile = self.require_s2_profile()
        result = self.run_s2(profile, S1_BASE)
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.output.read_bytes()
        self.assertEqual(after, s1, "no-change S2 must be byte-identical to S1")
        report = json.loads(
            self.output.with_suffix(".build.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report.get("changed_byte_count"), 0)
        self.assertEqual(report.get("changed_offsets"), [])
        self.assertEqual(report.get("output_sha256"), S1_PINNED_SHA256)
        self.assertEqual(report.get("source_sha256"), S1_PINNED_SHA256)


class S2NegativeTests(unittest.TestCase):
    """S2 rejection coverage. Guard tests pass now; S2-gated tests skip until S2-C."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_builder(self, profile_args, source=SOURCE, name="candidate.bin"):
        output = Path(self.tmp.name) / name
        return (
            subprocess.run(
                [sys.executable, str(BUILDER), str(source), str(output), *profile_args],
                capture_output=True,
                text=True,
            ),
            output,
        )

    def test_reject_soc_115v_setpoint(self):
        """SoC 1.15V as setpoint is OUT: no such profile may exist or be accepted."""
        self.assertEqual(
            set(builder_profiles()) & set(SOC_SETPOINT_DENYLIST),
            set(),
            "forbidden SoC-setpoint profile present",
        )
        for index, bogus in enumerate(SOC_SETPOINT_DENYLIST):
            result, output = self.run_builder(
                ["--profile", bogus], name="soc-%d.bin" % index
            )
            self.assertNotEqual(result.returncode, 0, "profile %s accepted" % bogus)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".build.json").exists())
        s2a = load_verdict(S2A_VERDICT)
        if s2a is not None:
            for entry in s2a.get("template", []):
                field = str(entry.get("field", ""))
                if "soc" in field.lower():
                    self.assertEqual(
                        entry.get("from"),
                        entry.get("to"),
                        "S2A changes SoC field %r (SoC setpoint OUT)" % field,
                    )

    def test_reject_vdd_offset_flags(self):
        """Explicit VDD-offset CLI flags are rejected unless S2-B closed the offset."""
        s2b = load_verdict(S2B_VERDICT)
        if s2b is not None and s2b.get("closed"):
            self.skipTest("S2-B closed the offset; flag rejection not applicable")
        for index, flags in enumerate(
            (("--vdd", "80"), ("--vdd-offset", "10"), ("--soc-voltage", "1150"))
        ):
            result, output = self.run_builder(
                ["--profile", "df1400", *flags], name="vddflag-%d.bin" % index
            )
            self.assertNotEqual(
                result.returncode, 0, "VDD flags %r accepted" % (flags,)
            )
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".build.json").exists())

    def test_s2_vdd_offset_gated_on_s2b(self):
        """VDD offset bytes change only with S2-B closure plus a stated value."""
        if not S1_BASE.exists():
            self.skipTest("S1 base image missing: %s" % S1_BASE)
        s1 = S1_BASE.read_bytes()
        for offset in VDD_OFFSET_BYTES:
            self.assertEqual(
                s1[offset], 0x00, "S1 base VDD offset %s not zero" % hex(offset)
            )
        profile = s2_profile()
        if profile is None:
            self.skipTest(
                "builder lacks S2 profile (has %s)" % sorted(builder_profiles())
            )
        s2b = load_verdict(S2B_VERDICT)
        if s2b is None:
            self.skipTest("S2-B verdict pending: %s" % S2B_VERDICT)
        output = Path(self.tmp.name) / "s2-vdd.bin"
        result = subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(S1_BASE),
                str(output),
                "--profile",
                profile,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        after = output.read_bytes()
        if not s2b.get("closed"):
            for offset in VDD_OFFSET_BYTES:
                self.assertEqual(
                    after[offset],
                    0x00,
                    "VDD offset written without S2-B closure at %s" % hex(offset),
                )
            changed = {i for i, (a, b) in enumerate(zip(s1, after)) if a != b}
            self.assertEqual(changed & set(VDD_OFFSET_BYTES), set())
        else:
            for key in ("consumer", "rail", "unit"):
                self.assertTrue(
                    str(s2b.get(key) or "").strip(), "closed S2-B lacks %s" % key
                )
            self.assertTrue(s2b.get("citations"), "closed S2-B lacks citations")
            value = s2b.get("value_u32")
            self.assertIsInstance(value, int, "closed S2-B lacks integer value_u32")
            self.assertTrue(
                vdd_bytes_match_value(after, value),
                "VDD bytes do not encode u32 %r: 0xBB4..0xBB8=%s"
                % (value, bytes(after[0xBB4:0xBB8]).hex()),
            )

    def test_reject_wrong_base_hash_s2(self):
        """S2 rejects any base that is not exactly the verified S1 image."""
        if not S1_BASE.exists():
            self.skipTest("S1 base image missing: %s" % S1_BASE)
        profile = s2_profile()
        if profile is None:
            self.skipTest(
                "builder lacks S2 profile (has %s)" % sorted(builder_profiles())
            )
        s1 = S1_BASE.read_bytes()
        cases = []
        for offset in (0x7E5, 0xBB4, 0xF5F, 0x30000):
            corrupted = bytearray(s1)
            corrupted[offset] ^= 0x01
            cases.append(("corrupt-%s" % hex(offset), bytes(corrupted)))
        cases.append(("truncated", s1[:0x20000]))
        for name, data in cases:
            bad_source = Path(self.tmp.name) / ("s2-%s.bin" % name)
            bad_source.write_bytes(data)
            output = Path(self.tmp.name) / ("s2-%s-out.bin" % name)
            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILDER),
                    str(bad_source),
                    str(output),
                    "--profile",
                    profile,
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0, "S2 accepted %s base" % name)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".build.json").exists())

    def test_reject_unknown_profile_s2(self):
        """Unknown S2-flavored profiles are rejected with no artifacts."""
        for index, bogus in enumerate(
            ("not-a-real-s2-profile", "s2-df1401", "s2-ocv-bogus")
        ):
            result, output = self.run_builder(
                ["--profile", bogus], name="s2bogus-%d.bin" % index
            )
            self.assertNotEqual(result.returncode, 0, "profile %s accepted" % bogus)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".build.json").exists())


if __name__ == "__main__":
    unittest.main()
