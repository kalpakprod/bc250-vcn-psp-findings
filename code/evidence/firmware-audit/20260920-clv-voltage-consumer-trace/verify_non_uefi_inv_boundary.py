#!/usr/bin/env python3
"""Boundary verifier for the CLV non-UEFI $INV/NVTB trace.

Read-only. Pins the immutable donor image, independently recomputes the $INV/NVTB
marker offsets and the u16 0x1363/0x1364 offsets, and answers the discriminator the
raw census in scan_non_uefi_inv.py cannot answer alone:

  is any 0x1363/0x1364 occurrence part of a structural $INV/NVTB record, or is it a
  coincidental u16 value with no container context?

V1 pinned ROM hash/size
V2 marker offsets + carrier attribution
V3 id offsets + carrier + mod4 + byte distance to the nearest marker
V4 structural assertion: every id occurrence sits >64 bytes from every marker
V5 cross-check of counts against Intent 2's scan JSON
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
ROM_SIZE = 16777216
PSP = ROOT / "evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json"
SCAN = ROOT / "evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-inv-scan.json"
OUT = ROOT / "evidence/firmware-audit/20260920-clv-voltage-consumer-trace/verify-non-uefi-inv-boundary.json"

MARKERS = {"$INV": b"$INV", "NVTB": b"NVTB"}
IDS = (0x1363, 0x1364)
ADJACENCY_BYTES = 64
# Flash map used for attribution only; every bound is an observed structural edge.
REGIONS = [
    (0x000000, 0x820000, "LOW_FLASH_0x0_0x820000"),
    (0x820000, 0x8E0000, "PRE_PSP_BLOCK_0x820000_0x8E0000"),
    (0x8E0000, 0xAE0000, "SIGNED_PSP_REGION_0x8E0000_0xAE0000"),
    (0xAE0000, 0xE00000, "FIRMWARE_REGION_0xAE0000_0xE00000"),
    (0xE00000, ROM_SIZE, "UEFI_FV_REGION_0xE00000_0x1000000"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_all(hay: bytes, needle: bytes) -> list[int]:
    out, i = [], hay.find(needle)
    while i != -1:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


def region_of(off: int) -> str:
    for a, b, name in REGIONS:
        if a <= off < b:
            return name
    return "OUT_OF_RANGE"


def main() -> int:
    rom = ROM.read_bytes()
    assert len(rom) == ROM_SIZE, len(rom)
    got = sha256(rom)
    assert got == ROM_SHA, got

    inv = json.loads(PSP.read_text())
    entries = sorted(
        ({"payload_id": e["payload_id"], "spi_offset": int(e["spi_offset"], 0),
          "size": int(e["size"])} for e in inv["psp_directory"]["entries"]),
        key=lambda r: r["spi_offset"])
    for r in entries:
        r["end"] = r["spi_offset"] + r["size"]

    def carrier_of(off: int) -> str:
        for r in entries:
            if r["spi_offset"] <= off < r["end"]:
                return f"PSP:{r['payload_id']}"
        return region_of(off)

    markers = {name: find_all(rom, magic) for name, magic in MARKERS.items()}
    all_marker_offs = sorted(o for offs in markers.values() for o in offs)

    id_hits = []
    for idv in IDS:
        pat = struct.pack("<H", idv)
        for off in find_all(rom, pat):
            nearest = min((abs(off - m) for m in all_marker_offs), default=None)
            id_hits.append({
                "id": f"0x{idv:04X}",
                "rom_offset": f"0x{off:X}",
                "carrier": carrier_of(off),
                "mod4": off % 4,
                "nearest_marker_bytes": nearest,
            })

    min_dist = min((h["nearest_marker_bytes"] for h in id_hits), default=None)
    violations = [h for h in id_hits if h["nearest_marker_bytes"] is not None
                  and h["nearest_marker_bytes"] <= ADJACENCY_BYTES]

    per_region: dict[str, int] = {}
    for h in id_hits:
        per_region[h["carrier"]] = per_region.get(h["carrier"], 0) + 1

    scan = json.loads(SCAN.read_text())
    cross = {
        "scan_markers": {k: scan["t2_markers_raw"][k]["count"] for k in MARKERS},
        "verifier_markers": {k: len(v) for k, v in markers.items()},
        "scan_ids": {f"0x{i:04X}": scan["t3_ids_raw"][f"0x{i:04X}"]["count"] for i in IDS},
        "verifier_ids": {f"0x{i:04X}": len(find_all(rom, struct.pack("<H", i))) for i in IDS},
    }
    cross["markers_agree"] = all(
        cross["scan_markers"][k] == cross["verifier_markers"][k] for k in MARKERS)
    cross["ids_agree"] = cross["scan_ids"] == cross["verifier_ids"]

    # Positive control: the adjacency metric must fire on a synthetic $INV record
    # (marker followed by a u16 token) so a clean image result is not vacuous.
    synthetic = b"$INV" + b"\x00\x00" + struct.pack("<H", 0x1363)
    ctrl_off = synthetic.find(struct.pack("<H", 0x1363))
    ctrl_dist = min(abs(ctrl_off - m) for m in find_all(synthetic, b"$INV"))
    positive_control = {"synthetic_marker_distance_bytes": ctrl_dist,
                        "fires": ctrl_dist <= ADJACENCY_BYTES}

    # Marker context: show that every $INV/NVTB marker is a code-side store immediate,
    # not a container record header.
    marker_context = {k: [{"rom_offset": f"0x{o:X}", "carrier": carrier_of(o),
                           "bytes_after_marker": rom[o:o + 16].hex(" ")}
                          for o in v] for k, v in markers.items()}

    result = {
        "tool": "verify_non_uefi_inv_boundary.py",
        "rom": {"path": str(ROM), "size": len(rom), "sha256": got},
        "adjacency_window_bytes": ADJACENCY_BYTES,
        "markers": {k: {"count": len(v), "offsets": [f"0x{o:X}" for o in v]}
                    for k, v in markers.items()},
        "marker_carriers": {k: sorted({carrier_of(o) for o in v}) for k, v in markers.items()},
        "id_hits": id_hits,
        "id_per_carrier": per_region,
        "min_marker_distance_bytes": min_dist,
        "adjacency_violations": violations,
        "positive_control": positive_control,
        "marker_context": marker_context,
        "verdict": ("NO_STRUCTURAL_INV_RECORD_OUTSIDE_UEFI_FV"
                    if not violations else "ADJACENT_RECORD_CONTEXT_FOUND"),
        "cross_check": cross,
    }
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "rom_sha256": got,
        "markers": cross["verifier_markers"],
        "marker_carriers": result["marker_carriers"],
        "id_per_carrier": per_region,
        "min_marker_distance_bytes": min_dist,
        "adjacency_violations": len(violations),
        "cross_check": {k: cross[k] for k in ("markers_agree", "ids_agree")},
        "positive_control": positive_control,
        "output": str(OUT),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
