#!/usr/bin/env python3
"""Bounded read-only search for $INV/NVTB carriers outside the 233-module UEFI corpus.

Pinned inputs only. Writes only its own JSON result next to this script.

T1  pinned-input hashes (ROM, PSP-directory inventory, 233-module census)
T2  literal markers b"$INV" (immediate 0x564E4924) and b"NVTB" (0x4254564E) over the
    whole image, attributed to PSP directory entry / extracted module / unattributed
T3  16-bit LE record ids 0x1363 and 0x1364 over the whole image, with alignment,
    byte context and extracted-module attribution
T4  structural tests over the whole image: (0x1363,0x1364) pair within 8 bytes, and an
    id immediately preceded by a 0xFFFF record terminator
T5  per PSP directory entry: locate the $PS1 container, zlib-decompress the signed body
    when the container declares compression, and repeat the marker/id search inside the
    decompressed image (the raw ROM scan in T2/T3 cannot see compressed payloads)
"""
from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
ROM_SIZE = 16777216
PSP = ROOT / "evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json"
CENSUS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/census.json"
MODULES = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
OUT = ROOT / "evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-inv-scan.json"

MARKERS = {"$INV": b"$INV", "NVTB": b"NVTB"}
IDS = (0x1363, 0x1364)
WINDOW = 48


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_all(hay: bytes, needle: bytes) -> list[int]:
    out, i = [], hay.find(needle)
    while i != -1:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


def main() -> int:
    rom = ROM.read_bytes()
    assert len(rom) == ROM_SIZE, len(rom)
    got = sha256(rom)
    assert got == ROM_SHA, got

    inv = json.loads(PSP.read_text())
    census = json.loads(CENSUS.read_text())
    entries = sorted(
        ({"payload_id": e["payload_id"], "type": e["type"],
          "spi_offset": int(e["spi_offset"], 0), "size": int(e["size"])}
         for e in inv["psp_directory"]["entries"]),
        key=lambda r: r["spi_offset"])
    for r in entries:
        r["end"] = r["spi_offset"] + r["size"]

    modules = {p.name: p.read_bytes() for p in sorted(MODULES.glob("*.bin"))}

    def carrier_of(off: int) -> str:
        for r in entries:
            if r["spi_offset"] <= off < r["end"]:
                return f"PSP:{r['payload_id']}"
        return "non-PSP"

    def attribute(off: int) -> list[str]:
        win = rom[off:off + WINDOW]
        if len(win) < 16:
            return []
        return [name for name, body in modules.items() if win in body]

    result = {
        "tool": "scan_non_uefi_inv.py",
        "inputs": {
            "rom": {"path": str(ROM), "size": len(rom), "sha256": got},
            "psp_inventory": {"path": str(PSP), "sha256": sha256(PSP.read_bytes()),
                              "size": PSP.stat().st_size},
            "census": {"path": str(CENSUS), "sha256": sha256(CENSUS.read_bytes()),
                       "records": len(census["records"])},
            "module_bodies": len(modules),
        },
        "psp_entries": [{"payload_id": r["payload_id"], "type": r["type"],
                         "spi_offset": f"0x{r['spi_offset']:X}", "size": r["size"]}
                        for r in entries],
    }

    # T2 markers over the raw image
    t2 = {}
    for label, pat in MARKERS.items():
        hits = []
        for i in find_all(rom, pat):
            hits.append({
                "rom_offset": f"0x{i:X}",
                "carrier": carrier_of(i),
                "attributed_modules": attribute(i),
                "context_hex": rom[max(0, i - 8):i + 16].hex(" "),
            })
        t2[label] = {"count": len(hits), "hits": hits}
    result["t2_markers_raw"] = t2

    # T3 ids over the raw image
    t3 = {}
    for idv in IDS:
        hits = []
        for off in find_all(rom, struct.pack("<H", idv)):
            hits.append({
                "rom_offset": f"0x{off:X}",
                "carrier": carrier_of(off),
                "mod4": off % 4,
                "attributed_modules": attribute(off),
                "context_hex": rom[max(0, off - 12):off + 16].hex(" "),
            })
        per_carrier: dict[str, int] = {}
        for h in hits:
            per_carrier[h["carrier"]] = per_carrier.get(h["carrier"], 0) + 1
        t3[f"0x{idv:04X}"] = {
            "count": len(hits),
            "per_carrier": per_carrier,
            "attributed_to_extracted_module": sum(1 for h in hits if h["attributed_modules"]),
            "in_psp_payload": sum(1 for h in hits if h["carrier"].startswith("PSP:")),
            "hits": hits,
        }
    result["t3_ids_raw"] = t3

    # T4 structural tests over the raw image
    a = find_all(rom, struct.pack("<H", 0x1363))
    b = find_all(rom, struct.pack("<H", 0x1364))
    pairs = [{"x": f"0x{x:X}", "y": f"0x{y:X}", "delta": y - x}
             for x in a for y in b if abs(y - x) <= 8]
    result["t4_structure_raw"] = {
        "pair_count_le8": len(pairs),
        "pairs": pairs,
        "preceded_by_ffff": [f"0x{x:X}" for x in a + b if rom[x - 2:x] == b"\xff\xff"],
    }

    # T5 decompressed $PS1 payloads
    t5 = []
    for r in entries:
        blob = rom[r["spi_offset"]:r["end"]]
        rec = {"payload_id": r["payload_id"], "type": r["type"],
               "spi_offset": f"0x{r['spi_offset']:X}", "container_size": len(blob),
               "is_ps1": None, "compressed": None, "decompressed_size": None,
               "decompressed_sha256": None, "decompression_error": None,
               "markers": {}, "ids": {}}
        if blob[0x10:0x14] == b"$PS1":
            signed = struct.unpack_from("<I", blob, 0x14)[0]
            compressed = struct.unpack_from("<I", blob, 0x48)[0]
            rec["is_ps1"] = True
            rec["compressed"] = compressed
            body = blob[0x100:0x100 + signed]
            img = body
            if compressed == 1:
                try:
                    img = zlib.decompress(body)
                    rec["decompressed_size"] = len(img)
                    rec["decompressed_sha256"] = sha256(img)
                except Exception as exc:  # retained as text
                    rec["decompression_error"] = f"{type(exc).__name__}: {exc}"
                    img = None
            elif compressed not in (0, 1):
                rec["decompression_error"] = f"unexpected compressed flag {compressed}"
                img = None
            else:
                rec["decompressed_size"] = len(img)
                rec["decompressed_sha256"] = sha256(img)
            if img is not None:
                for label, pat in MARKERS.items():
                    offs = find_all(img, pat)
                    rec["markers"][label] = {"count": len(offs),
                                             "offsets": [f"0x{o:X}" for o in offs]}
                for idv in IDS:
                    offs = find_all(img, struct.pack("<H", idv))
                    rec["ids"][f"0x{idv:04X}"] = {
                        "count": len(offs),
                        "mod4": [o % 4 for o in offs],
                        "contexts": [img[max(0, o - 12):o + 16].hex(" ") for o in offs],
                    }
            rec["isa_entry_first16"] = img[:16].hex() if img else None
        else:
            rec["is_ps1"] = False
            rec["markers"] = {k: {"count": len(find_all(blob, v)),
                                  "offsets": [f"0x{o:X}" for o in find_all(blob, v)]}
                              for k, v in MARKERS.items()}
            for idv in IDS:
                offs = find_all(blob, struct.pack("<H", idv))
                rec["ids"][f"0x{idv:04X}"] = {"count": len(offs),
                                              "mod4": [o % 4 for o in offs],
                                              "contexts": [blob[max(0, o - 12):o + 16].hex(" ") for o in offs]}
        t5.append(rec)
    result["t5_psp_payloads"] = t5

    # T5 summary: any marker or id inside a decompressed payload
    dec_marker_hits = {k: [] for k in MARKERS}
    dec_id_hits = {f"0x{i:04X}": [] for i in IDS}
    for rec in t5:
        for k in MARKERS:
            if rec["markers"].get(k, {}).get("count"):
                dec_marker_hits[k].append(rec["payload_id"])
        for k in dec_id_hits:
            if rec["ids"].get(k, {}).get("count"):
                dec_id_hits[k].append(rec["payload_id"])
    result["t5_summary"] = {"marker_payloads": dec_marker_hits,
                            "id_payloads": dec_id_hits}

    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "PASS",
        "rom_sha256": got,
        "psp_entries": len(entries),
        "t2_markers_raw": {k: v["count"] for k, v in t2.items()},
        "t2_marker_carriers": {k: sorted({h["carrier"] for h in v["hits"]}) for k, v in t2.items()},
        "t3_ids_raw": {k: {"total": v["count"], "attributed": v["attributed_to_extracted_module"],
                           "in_psp": v["in_psp_payload"]} for k, v in t3.items()},
        "t4_pair_count_le8": result["t4_structure_raw"]["pair_count_le8"],
        "t4_preceded_by_ffff": result["t4_structure_raw"]["preceded_by_ffff"],
        "t5_payloads_with_marker": result["t5_summary"]["marker_payloads"],
        "t5_payloads_with_id": result["t5_summary"]["id_payloads"],
        "output": str(OUT),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
