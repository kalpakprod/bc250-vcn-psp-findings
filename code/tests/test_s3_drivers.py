"""S3 driver-injection tests (S3-F).

Positive: 6 drivers present by GUID, FFS 187->193, S1 NVRAM intact in S3,
provenance schema, unhide-applied-iff-S3B-go (plus PSP/APCB identity of S3
vs S2 as the artifact side of the delta gate).

Negative (helper gates, always runnable): reject wrong-base-hash, reject
missing driver, reject PSP/APCB delta, reject unhide-without-verdict.

Builder CLI rejection tests skip until scripts/build_s3_drivers.py lands
(S3-C). Every test that needs a not-yet-built S3 artifact skips with a
reason instead of failing. This file is new; test_clv_oc_builder.py is
untouched.

Run: pytest tests/test_s3_drivers.py -v
  or: python3 -m unittest tests.test_s3_drivers -v
"""

import hashlib
import json
import lzma
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S2_BASE = ROOT / "candidates/s2-ocv/BC250_5.00_clv_S2-OCV_v001.bin"
S2_PINNED_SHA256 = "c5dc6424b3d836b0a262ed54d9c3e747f2c33d40cb614fac40e4ea46e7bfbf7c"
CLV_BASE = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
S3_CAND = ROOT / "candidates/s3-drivers/BC250_5.00_clv_S3-DRV_v001.bin"
S3A_VERDICT = ROOT / "candidates/s3-drivers/S3A-verdict.json"
S3B_VERDICT = ROOT / "candidates/s3-drivers/S3B-verdict.json"
S3_PROV = ROOT / "candidates/s3-drivers/S3-DRV_v001.provenance.json"
FD_BUILDER = ROOT / "scripts/build_fd_drivers_clv.py"
S3_BUILDER = ROOT / "scripts/build_s3_drivers.py"
FD_DONOR = (
    ROOT
    / "archives/imported/external-tool-packs/legacy-tmp-bc250-ext/fd_repo/extracted/BC250_3.00_MeiMeiDXEv3"
)
DRIVERS_ONLY_REF = ROOT / "candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin"

# 6-driver MeiMeiDXEv3 set, per scripts/build_fd_drivers_clv.py MEIMEI and the
# 0968a70c build.json (fd-v22-to-clv-port). S3 replays this exact set on S2.
EXPECTED_DRIVERS = (
    ("A3F8B2D5-7C4E-4F0A-B1D2-9E6F3C8A5B71", "MeiMeiDXEv3_SMU_Unlock"),
    ("7A8B9C0D-1E2F-3A4B-5C6D-7E8F9A0B1C2D", "MeiMeiDXEv3_SMU_Core_Unlock"),
    ("0DDDE9E4-4A0C-4679-BEDC-90A37610AB85", "MeiMeiDXEv3_Menu_Driver"),
    ("A9981D14-6329-4698-AD20-173C4363DD30", "MeiMeiDXEv3_ACPI_AutoInject"),
    ("9D4E5E12-3C7A-4F88-A2B7-0D8D6B7F2E41", "MeiMeiDXEv3_SMU_Patch"),
    ("6C98E4F3-9D8B-4E5A-B2E7-31A45B9C5D81", "MeiMeiDXEv3_ColdBoot"),
)
EXPECTED_GUIDS = frozenset(g for g, _ in EXPECTED_DRIVERS)

# S1 NVRAM bytes that S2/S3 must preserve (ROM-absolute).
S1_PRESERVED = {
    0x7E5: 0x1A,
    0x7FF: 0x01,
    0x83C: 0xFF,
    0xBD2: 0x01,
    0xBD3: 0x32,
    0xBD4: 0x05,
}
S1_DF_U16 = 0x0532
IMAGE_SIZE = 0x1000000

OUTER_FV = 0xAE0000
OUTER_LEN = 0x320000
CAPSULE_GUID = bytes.fromhex("93fd219e729c154c8c4be77f1db2d792")
PSP_OFF = 0x8E0000
BHD_OFF = 0xAB0000
APCB_OFF = 0xAB1000
APCB_WINDOW = 0xB9C
S2_FFS_EXPECTED = 187
S3_FFS_EXPECTED = 193

# Out-of-S3 per S3-B brief: must never be claimed as applied in S3.
OUT_OF_S3_MARKERS = ("B1DA0ADF", "7BB28B99")

FFS_TYPES = frozenset(
    {
        0x01,
        0x02,
        0x03,
        0x04,
        0x05,
        0x06,
        0x07,
        0x08,
        0x09,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x0E,
        0x0F,
        0xF0,
    }
)

_INNER_CACHE = {}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def guid_str(raw: bytes) -> str:
    raw = bytes(raw[:16])
    a, b, c = struct.unpack("<IHH", raw[:8])
    return f"{a:08X}-{b:04X}-{c:04X}-{raw[8:10].hex().upper()}-{raw[10:].hex().upper()}"


def walk_inner_fv(fv: bytes):
    """Inventory an inner FV. Returns (files, fv_length). Raises ValueError."""
    if fv[0x28:0x2C] != b"_FVH":
        raise ValueError("inner FV missing _FVH signature")
    flen = struct.unpack_from("<Q", fv, 0x20)[0]
    hdrlen = struct.unpack_from("<H", fv, 0x30)[0]
    if flen > len(fv):
        raise ValueError("inner FV length exceeds buffer")
    if hdrlen != 0x48:
        raise ValueError(f"unexpected inner FV header length {hdrlen:#x}")
    inv, pos = [], 0x48
    while pos + 24 <= flen:
        h = bytes(fv[pos : pos + 24])
        typ = h[18]
        if typ in FFS_TYPES:
            size = int.from_bytes(h[20:23], "little")
            cksum_ok = (sum(h[:17]) + sum(h[18:23])) & 0xFF == 0
            if size >= 24 and pos + size <= flen and cksum_ok:
                inv.append(
                    {
                        "guid": guid_str(h),
                        "type": typ,
                        "size": size,
                        "off": pos,
                        "sha": sha256(bytes(fv[pos + 24 : pos + size])),
                    }
                )
                pos = (pos + size + 7) & ~7
                continue
        if bytes(fv[pos : pos + 8]) == b"\xff" * 8:
            pos += 8
            continue
        raise ValueError(f"FFS walk stops at {pos:#x}: {h.hex()}")
    return inv, flen


def decompress_inner(img: bytes):
    """Unwrap capsule GUIDED(LZMA) to the inner FV bytes. Raises ValueError."""
    cpos = img.find(CAPSULE_GUID, OUTER_FV, OUTER_FV + 0x1000)
    if cpos <= 0 or cpos % 8:
        raise ValueError("capsule FFS not found at expected alignment")
    if img[cpos + 18] != 0x0B:
        raise ValueError("capsule FFS has unexpected type")
    csz = int.from_bytes(img[cpos + 20 : cpos + 23], "little")
    data = img[cpos + 24 : cpos + csz]
    if len(data) < 24 or data[3] != 0x02:
        raise ValueError("capsule is not GUID_DEFINED")
    gsz = int.from_bytes(data[0:3], "little")
    if gsz != len(data):
        raise ValueError("GUIDED size mismatch")
    doff = int.from_bytes(data[20:22], "little")
    inner = lzma.decompress(bytes(data[doff:]), format=lzma.FORMAT_ALONE)
    if inner[3] != 0x19:
        raise ValueError("inner stream is not RAW")
    rsz = int.from_bytes(inner[0:3], "little")
    pad = (rsz + 3) & ~3
    if inner[pad + 3] != 0x17:
        raise ValueError("inner stream lacks FV_IMAGE section")
    fsz = int.from_bytes(inner[pad : pad + 3], "little")
    fv = bytes(inner[pad + 4 : pad + fsz])
    return {"cpos": cpos, "csz": csz, "fv": fv}


def inner_inventory_of_file(path: Path):
    """Cached (inv, flen) for an on-disk image. Files are never written."""
    key = str(path.resolve())
    hit = _INNER_CACHE.get(key)
    if hit is not None:
        return hit
    img = path.read_bytes()
    inv, flen = walk_inner_fv(decompress_inner(img)["fv"])
    _INNER_CACHE[key] = (inv, flen)
    return inv, flen


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def psp_dir_bytes(img: bytes) -> bytes:
    count = struct.unpack_from("<H", img, PSP_OFF + 8)[0]
    return bytes(img[PSP_OFF : PSP_OFF + 16 + 16 * count])


def bhd_dir_bytes(img: bytes) -> bytes:
    count = struct.unpack_from("<I", img, BHD_OFF + 8)[0]
    count = min(count, 64)  # sanity cap; S2 carries 4 entries
    return bytes(img[BHD_OFF : BHD_OFF + 0x10 + 24 * count])


def apcb_window_bytes(img: bytes) -> bytes:
    return bytes(img[APCB_OFF : APCB_OFF + APCB_WINDOW])


# ---- Rejection gates mirroring the contract the S3 builder must enforce. ----


def gate_base_hash(image: bytes, expected_sha256: str) -> None:
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"base size {len(image)} != {IMAGE_SIZE:#x}")
    actual = sha256(image)
    if actual != expected_sha256:
        raise ValueError(f"base hash {actual} != pinned {expected_sha256}")


def gate_drivers_present(found_guids: set, expected=EXPECTED_DRIVERS) -> None:
    missing = [g for g, _ in expected if g not in found_guids]
    if missing:
        raise ValueError(f"missing drivers: {', '.join(missing)}")


def gate_no_protected_delta(base: bytes, cand: bytes) -> None:
    if len(base) != len(cand):
        raise ValueError("protected-delta check requires equal-size images")
    if psp_dir_bytes(cand) != psp_dir_bytes(base):
        raise ValueError("PSP directory delta rejected")
    if bhd_dir_bytes(cand) != bhd_dir_bytes(base):
        raise ValueError("BHD directory delta rejected")
    if apcb_window_bytes(cand) != apcb_window_bytes(base):
        raise ValueError("APCB window delta rejected")


def gate_unhide(verdict, unhide_requested: bool) -> None:
    if unhide_requested and (not verdict or not verdict.get("unhide_go")):
        raise ValueError("unhide requested without S3B unhide_go=true")


def provenance_unhide_status(prov: dict) -> str:
    """Return 'applied', 'skipped', or 'unknown' for the provenance record."""
    for key, value in prov.items():
        low = str(key).lower()
        if "unhide" in low or "setup_unhide" in low:
            if isinstance(value, bool):
                return "applied" if value else "skipped"
            if isinstance(value, dict) and "applied" in value:
                applied = value["applied"]
                return "applied" if applied else "skipped"
            text = json.dumps(value).lower()
            if "appl" in text and "not appl" not in text and "unapplied" not in text:
                return "applied"
            if any(
                tag in text for tag in ("skip", "defer", "false", "none", "not applied")
            ):
                return "skipped"
    blob = json.dumps(prov).lower()
    if "unhide" not in blob:
        return "unknown"
    if (
        "unhide applied" in blob
        or '"unhide": true' in blob
        or 'unhide_go": true' in blob
    ):
        return "applied"
    if any(
        tag in blob
        for tag in (
            "unhide skipped",
            "unhide deferred",
            "without unhide",
            "no unhide",
            'unhide": false',
            'unhide_go": false',
        )
    ):
        return "skipped"
    return "unknown"


def s3_builder_path():
    return S3_BUILDER if S3_BUILDER.exists() else None


def builder_help_text(builder: Path) -> str:
    try:
        proc = subprocess.run(
            [sys.executable, str(builder), "--help"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return (proc.stdout or "") + (proc.stderr or "")


class S3PreconditionTests(unittest.TestCase):
    """S2/donor/lineage facts S3 builds on. Pass on the current checkout."""

    def test_s2_base_pinned(self):
        if not S2_BASE.exists():
            self.skipTest(f"S2 base missing: {S2_BASE}")
        data = S2_BASE.read_bytes()
        self.assertEqual(len(data), IMAGE_SIZE)
        self.assertEqual(sha256(data), S2_PINNED_SHA256)

    def test_s2_inner_fv_has_187(self):
        if not S2_BASE.exists():
            self.skipTest(f"S2 base missing: {S2_BASE}")
        inv, flen = inner_inventory_of_file(S2_BASE)
        self.assertEqual(
            len(inv), S2_FFS_EXPECTED, f"S2 inner FV has {len(inv)} files, want 187"
        )
        self.assertEqual(flen, 0x41C000)

    def test_s2_lacks_6_drivers(self):
        if not S2_BASE.exists():
            self.skipTest(f"S2 base missing: {S2_BASE}")
        inv, _ = inner_inventory_of_file(S2_BASE)
        guids = {f["guid"] for f in inv}
        present = [g for g, _ in EXPECTED_DRIVERS if g in guids]
        self.assertEqual(present, [], f"S2 already carries {present}")

    def test_s2_s1_nvram_intact(self):
        if not S2_BASE.exists():
            self.skipTest(f"S2 base missing: {S2_BASE}")
        data = S2_BASE.read_bytes()
        for offset, value in S1_PRESERVED.items():
            self.assertEqual(data[offset], value, f"S2 ROM {offset:#x}")
        self.assertEqual(int.from_bytes(data[0xBD3:0xBD5], "little"), S1_DF_U16)

    def test_fd_donor_has_6_drivers(self):
        if not FD_DONOR.exists():
            self.skipTest(f"FD donor missing: {FD_DONOR}")
        inv, _ = inner_inventory_of_file(FD_DONOR)
        guids = {f["guid"] for f in inv}
        gate_drivers_present(guids)  # raises listing any missing driver

    def test_fd_builder_present(self):
        self.assertTrue(FD_BUILDER.exists(), f"FD builder missing: {FD_BUILDER}")

    def test_drivers_only_lineage_193(self):
        """0968a70c lineage proof: CLV + 6 drivers == 193 files."""
        if not DRIVERS_ONLY_REF.exists():
            self.skipTest(f"drivers-only reference missing: {DRIVERS_ONLY_REF}")
        inv, _ = inner_inventory_of_file(DRIVERS_ONLY_REF)
        self.assertEqual(len(inv), S3_FFS_EXPECTED)
        gate_drivers_present({f["guid"] for f in inv})


class S3PositiveTests(unittest.TestCase):
    """S3 artifact checks. Skip (not fail) until S3-C builds the image."""

    def require_s3(self) -> bytes:
        if not S3_CAND.exists():
            self.skipTest(f"S3 candidate not built yet: {S3_CAND}")
        data = S3_CAND.read_bytes()
        self.assertEqual(len(data), IMAGE_SIZE)
        return data

    def test_6_drivers_present_by_guid(self):
        self.require_s3()
        inv, _ = inner_inventory_of_file(S3_CAND)
        guids = {f["guid"] for f in inv}
        try:
            gate_drivers_present(guids)
        except ValueError as error:
            self.fail(str(error))
        if S3A_VERDICT.exists():
            s3a = load_json(S3A_VERDICT)
            if s3a is not None:
                inputs = s3a.get("inputs", []) or []
                verdict_guids = {
                    str(item.get("guid", "")).upper()
                    for item in inputs
                    if isinstance(item, dict)
                }
                self.assertEqual(
                    verdict_guids,
                    set(EXPECTED_GUIDS),
                    "S3A input GUIDs != arbitrated 6-driver set",
                )
        if FD_DONOR.exists():
            donor_inv, _ = inner_inventory_of_file(FD_DONOR)
            donor_sha = {f["guid"]: f["sha"] for f in donor_inv}
            s3_sha = {f["guid"]: f["sha"] for f in inv}
            for guid, _ in EXPECTED_DRIVERS:
                self.assertEqual(
                    s3_sha[guid],
                    donor_sha[guid],
                    f"driver {guid} body differs from donor",
                )

    def test_ffs_187_to_193(self):
        if not S2_BASE.exists():
            self.skipTest(f"S2 base missing: {S2_BASE}")
        self.require_s3()
        s2_inv, _ = inner_inventory_of_file(S2_BASE)
        s3_inv, _ = inner_inventory_of_file(S3_CAND)
        self.assertEqual(len(s2_inv), S2_FFS_EXPECTED)
        self.assertEqual(len(s3_inv), S3_FFS_EXPECTED)
        self.assertEqual(len(s3_inv) - len(s2_inv), 6)
        s2_guids = [f["guid"] for f in s2_inv]
        s3_guids = [f["guid"] for f in s3_inv]
        self.assertEqual(
            set(s2_guids) - set(s3_guids), set(), "S3 dropped native S2 files"
        )
        added = set(s3_guids) - set(s2_guids)
        self.assertEqual(
            added,
            set(EXPECTED_GUIDS),
            f"S3 added GUIDs != 6-driver set: {sorted(added)}",
        )

    def test_s1_nvram_intact_in_s3(self):
        data = self.require_s3()
        for offset, value in S1_PRESERVED.items():
            self.assertEqual(data[offset], value, f"S3 ROM {offset:#x}")
        self.assertEqual(int.from_bytes(data[0xBD3:0xBD5], "little"), S1_DF_U16)
        if S2_BASE.exists():
            s2 = S2_BASE.read_bytes()
            self.assertEqual(
                bytes(data[:OUTER_FV]),
                bytes(s2[:OUTER_FV]),
                "S3 bytes before 0xAE0000 differ from S2",
            )

    def test_psp_apcb_identical_to_s2(self):
        """Artifact side of the delta gate: S3 must carry S2's PSP/BHD/APCB."""
        data = self.require_s3()
        if not S2_BASE.exists():
            self.skipTest(f"S2 base missing: {S2_BASE}")
        try:
            gate_no_protected_delta(S2_BASE.read_bytes(), data)
        except ValueError as error:
            self.fail(str(error))

    def test_provenance_schema(self):
        if not S3_PROV.exists():
            self.skipTest(f"S3 provenance not built yet: {S3_PROV}")
        prov = load_json(S3_PROV)
        self.assertIsInstance(prov, dict, "provenance is not a JSON object")
        blob = json.dumps(prov)
        upper = blob.upper()
        self.assertIn(S2_PINNED_SHA256, blob, "provenance lacks the S2 base hash")
        for guid, _ in EXPECTED_DRIVERS:
            self.assertIn(guid, upper, f"provenance lacks driver {guid}")
        self.assertIn("187", blob, "provenance lacks the 187 baseline count")
        self.assertIn("193", blob, "provenance lacks the 193 target count")
        self.assertTrue(
            "REQUEST_ONLY" in blob or "NOT_FLASH_APPROVED" in blob,
            "provenance lacks a request-only label",
        )
        self.assertTrue(
            any("unhide" in str(key).lower() for key in prov)
            or "unhide" in blob.lower(),
            "provenance lacks an unhide applied/skipped record",
        )
        self.assertTrue(
            any(
                key in prov
                for key in ("injected", "drivers", "changed_bytes", "inputs")
            ),
            "provenance lacks an injected/changed record",
        )
        lowered = blob.lower()
        self.assertTrue(
            "s2-ocv" in lowered or "s2_ocv" in lowered or "s2" in lowered,
            "provenance does not reference the S2 base",
        )
        for marker in OUT_OF_S3_MARKERS:
            injected = prov.get("injected", prov.get("drivers", [])) or []
            if isinstance(injected, list):
                guids = json.dumps(injected).upper()
                self.assertNotIn(
                    marker, guids, f"out-of-S3 marker {marker} claimed injected"
                )
        if S3_CAND.exists():
            actual = sha256(S3_CAND.read_bytes())
            for key in ("output_hash", "output_sha256", "sha256"):
                if key in prov:
                    self.assertEqual(
                        str(prov[key]).lower(),
                        actual,
                        f"provenance {key} != S3 file hash",
                    )
                    break
            else:
                self.fail("provenance has no output_hash/output_sha256 key")

    def test_unhide_applied_iff_s3b_go(self):
        s3b = load_json(S3B_VERDICT)
        if s3b is None:
            self.skipTest(f"S3B verdict pending: {S3B_VERDICT}")
        prov = load_json(S3_PROV)
        if prov is None:
            self.skipTest(f"S3 provenance not built yet: {S3_PROV}")
        self.assertIn("unhide_go", s3b, "S3B verdict lacks unhide_go")
        self.assertIsInstance(s3b["unhide_go"], bool, "S3B unhide_go is not bool")
        unhide_go = s3b["unhide_go"]
        status = provenance_unhide_status(prov)
        if unhide_go:
            self.assertEqual(
                status,
                "applied",
                "S3B says UNHIDE-GO but provenance lacks applied record",
            )
        else:
            self.assertEqual(
                status,
                "skipped",
                "S3B says DEFERRED but provenance lacks skipped record",
            )
        changes = s3b.get("changes", []) or []
        if unhide_go:
            self.assertTrue(changes, "UNHIDE-GO verdict lists no byte changes")
        for change in changes:
            self.assertIn("file", change, "unhide change lacks file")
            blob = json.dumps(prov)
            self.assertIn(
                str(change["file"]).upper().replace("-", ""),
                blob.upper().replace("-", ""),
                f"provenance omits unhide file {change['file']}",
            )
        if S3_CAND.exists() and S2_BASE.exists() and changes:
            s2, s3 = S2_BASE.read_bytes(), S3_CAND.read_bytes()
            rom_absolute = True
            for change in changes:
                try:
                    offset = (
                        int(str(change["offset"]), 16)
                        if isinstance(change.get("offset"), str)
                        else int(change["offset"])
                    )
                    old = (
                        int(str(change["old"]), 16)
                        if isinstance(change.get("old"), str)
                        else int(change["old"])
                    )
                except (KeyError, TypeError, ValueError):
                    rom_absolute = False
                    break
                if not 0 <= offset < IMAGE_SIZE or s2[offset] != old:
                    rom_absolute = False
                    break
            if not rom_absolute:
                # File-relative offsets: inner-FV byte proof belongs to S3-E.
                # Verdict/provenance consistency above already passed.
                return
            for change in changes:
                offset = (
                    int(str(change["offset"]), 16)
                    if isinstance(change.get("offset"), str)
                    else int(change["offset"])
                )
                old = (
                    int(str(change["old"]), 16)
                    if isinstance(change.get("old"), str)
                    else int(change["old"])
                )
                new = (
                    int(str(change["new"]), 16)
                    if isinstance(change.get("new"), str)
                    else int(change["new"])
                )
                if unhide_go:
                    self.assertEqual(
                        s3[offset], new, f"unhide byte {offset:#x} not applied"
                    )
                else:
                    self.assertEqual(
                        s3[offset], old, f"unhide byte {offset:#x} written without GO"
                    )


class S3NegativeHelperTests(unittest.TestCase):
    """Gate-logic rejection tests. Runnable before S3-C lands."""

    def test_reject_wrong_base_hash(self):
        if not S2_BASE.exists():
            self.skipTest(f"S2 base missing: {S2_BASE}")
        good = S2_BASE.read_bytes()
        gate_base_hash(good, S2_PINNED_SHA256)  # sanity: pinned base passes
        for offset in (0x7E5, 0xBD3, 0x30000):
            bad = bytearray(good)
            bad[offset] ^= 0x01
            with self.assertRaises(ValueError, msg=f"corrupt {offset:#x} accepted"):
                gate_base_hash(bytes(bad), S2_PINNED_SHA256)
        with self.assertRaises(ValueError, msg="truncated base accepted"):
            gate_base_hash(good[:0x20000], S2_PINNED_SHA256)
        if CLV_BASE.exists():
            with self.assertRaises(ValueError, msg="CLV lineage accepted as S3 base"):
                gate_base_hash(CLV_BASE.read_bytes(), S2_PINNED_SHA256)

    def test_reject_missing_driver(self):
        full = set(EXPECTED_GUIDS)
        gate_drivers_present(full)  # sanity: full set passes
        for guid in sorted(full):
            with self.assertRaises(ValueError, msg=f"missing {guid} accepted"):
                gate_drivers_present(full - {guid})
        with self.assertRaises(ValueError, msg="empty driver set accepted"):
            gate_drivers_present(set())
        if S2_BASE.exists():
            inv, _ = inner_inventory_of_file(S2_BASE)
            with self.assertRaises(ValueError, msg="S2 native set accepted as S3"):
                gate_drivers_present({f["guid"] for f in inv})

    def test_reject_psp_apcb_delta(self):
        if not S2_BASE.exists():
            self.skipTest(f"S2 base missing: {S2_BASE}")
        base = S2_BASE.read_bytes()
        gate_no_protected_delta(base, bytes(base))  # sanity: identical passes
        for offset in (PSP_OFF + 0x10, BHD_OFF + 0x10, APCB_OFF + 0x20):
            bad = bytearray(base)
            bad[offset] ^= 0x01
            with self.assertRaises(ValueError, msg=f"delta at {offset:#x} accepted"):
                gate_no_protected_delta(base, bytes(bad))
        benign = bytearray(base)  # outside protected windows: gate stays silent
        benign[0x30000] ^= 0x01
        gate_no_protected_delta(base, bytes(benign))

    def test_reject_unhide_without_verdict(self):
        gate_unhide(None, False)
        gate_unhide({"unhide_go": False}, False)
        gate_unhide({"unhide_go": True}, True)
        gate_unhide({"unhide_go": True}, False)
        with self.assertRaises(ValueError, msg="unhide without verdict accepted"):
            gate_unhide(None, True)
        with self.assertRaises(ValueError, msg="unhide with deferred verdict accepted"):
            gate_unhide({"unhide_go": False, "changes": []}, True)
        live = load_json(S3B_VERDICT)
        if live is not None and not live.get("unhide_go"):
            with self.assertRaises(
                ValueError, msg="unhide accepted despite S3B deferral"
            ):
                gate_unhide(live, True)


class S3BuilderRejectionTests(unittest.TestCase):
    """S3 builder CLI rejection tests. Skip until S3-C lands the builder."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def require_builder(self) -> Path:
        builder = s3_builder_path()
        if builder is None:
            self.skipTest(f"S3 builder not landed yet: {S3_BUILDER}")
        return builder

    def require_cli(self, builder: Path) -> str:
        help_text = builder_help_text(builder)
        needles = (
            "--s2-base",
            "--donor",
            "--s3a-verdict",
            "--s3b-verdict",
            "--output",
            "--provenance",
        )
        missing = [needle for needle in needles if needle not in help_text]
        if missing:
            self.skipTest(f"S3 builder CLI lacks {missing}; help: {help_text[:200]!r}")
        return help_text

    def require_inputs(self):
        for path, label in (
            (S2_BASE, "S2 base"),
            (FD_DONOR, "FD donor"),
            (S3A_VERDICT, "S3A verdict"),
            (S3B_VERDICT, "S3B verdict"),
        ):
            if not path.exists():
                self.skipTest(f"{label} missing: {path}")

    def run_s3(
        self,
        builder: Path,
        s2_base: Path,
        donor: Path,
        s3a: Path,
        s3b: Path,
        output: Path,
        provenance: Path | None = None,
    ) -> subprocess.CompletedProcess:
        prov = provenance or output.with_suffix(".provenance.json")
        return subprocess.run(
            [
                sys.executable,
                str(builder),
                "--s2-base",
                str(s2_base),
                "--donor",
                str(donor),
                "--s3a-verdict",
                str(s3a),
                "--s3b-verdict",
                str(s3b),
                "--output",
                str(output),
                "--provenance",
                str(prov),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

    def test_builder_rejects_wrong_base_hash(self):
        builder = self.require_builder()
        self.require_cli(builder)
        self.require_inputs()
        bad = bytearray(S2_BASE.read_bytes())
        bad[0x30000] ^= 0x01
        bad_path = Path(self.tmp.name) / "bad-base.bin"
        bad_path.write_bytes(bad)
        output = Path(self.tmp.name) / "wrong-base-out.bin"
        result = self.run_s3(
            builder, bad_path, FD_DONOR, S3A_VERDICT, S3B_VERDICT, output
        )
        self.assertNotEqual(result.returncode, 0, "builder accepted corrupt base")
        self.assertFalse(output.exists())
        self.assertFalse(output.with_suffix(".provenance.json").exists())
        if CLV_BASE.exists():
            clv_out = Path(self.tmp.name) / "clv-lineage-out.bin"
            lineage = self.run_s3(
                builder, CLV_BASE, FD_DONOR, S3A_VERDICT, S3B_VERDICT, clv_out
            )
            self.assertNotEqual(
                lineage.returncode, 0, "builder accepted CLV lineage as S3 base"
            )
            self.assertFalse(clv_out.exists())

    def test_builder_rejects_missing_driver(self):
        builder = self.require_builder()
        self.require_cli(builder)
        self.require_inputs()
        # S2 as donor carries 0/6 drivers, so injection must fail fast.
        output = Path(self.tmp.name) / "missing-driver-out.bin"
        result = self.run_s3(
            builder, S2_BASE, S2_BASE, S3A_VERDICT, S3B_VERDICT, output
        )
        self.assertNotEqual(result.returncode, 0, "builder accepted driverless donor")
        self.assertFalse(output.exists())
        self.assertFalse(output.with_suffix(".provenance.json").exists())

    def test_builder_rejects_unhide_without_verdict(self):
        builder = self.require_builder()
        self.require_cli(builder)
        self.require_inputs()
        # (a) Missing S3B verdict file: the unhide gate has no authority.
        output = Path(self.tmp.name) / "unhide-no-verdict.bin"
        missing = Path(self.tmp.name) / "no-s3b.json"
        result = self.run_s3(builder, S2_BASE, FD_DONOR, S3A_VERDICT, missing, output)
        self.assertNotEqual(result.returncode, 0, "builder ran without S3B verdict")
        self.assertFalse(output.exists())
        # (b) UNHIDE-GO with an empty change list: nothing authorizes any byte.
        hollow = Path(self.tmp.name) / "hollow-s3b.json"
        hollow.write_text(json.dumps({"unhide_go": True, "changes": []}))
        hollow_out = Path(self.tmp.name) / "unhide-hollow-out.bin"
        hollow_result = self.run_s3(
            builder, S2_BASE, FD_DONOR, S3A_VERDICT, hollow, hollow_out
        )
        self.assertNotEqual(
            hollow_result.returncode, 0, "builder accepted UNHIDE-GO with no changes"
        )
        self.assertFalse(hollow_out.exists())


if __name__ == "__main__":
    unittest.main()
