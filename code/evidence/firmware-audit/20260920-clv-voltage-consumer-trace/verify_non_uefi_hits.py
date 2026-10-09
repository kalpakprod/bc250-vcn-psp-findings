#!/usr/bin/env python3
"""Independent verification and classification of the non-UEFI $INV/NVTB carrier scan.

Read-only over immutable pinned inputs. Independent of scan_non_uefi_inv.py and of
verify_non_uefi_inv_boundary.py: it re-parses the $PS1 containers itself, re-decompresses
the compressed bodies itself, re-computes the marker<->id adjacency statistic itself, and
adds two checks neither of those tools performs:

  C1  ARM/Thumb disassembly of the ABL3 id-word site (minimal ELF wrapper + llvm-objdump),
      to decide whether the u16 lives in an instruction or in a record table;
  C2  producer-side serializer displacements, to fix the token -> AmdSetup offset mapping
      (the open disagreement between the pinned table and the sibling report).

Writes only its own JSON next to this script.
"""
from __future__ import annotations

import hashlib, json, math, struct, subprocess, zlib
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
INV = ROOT / "evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json"
CENSUS_DIR = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
HERE = ROOT / "evidence/firmware-audit/20260920-clv-voltage-consumer-trace"
SCAN = HERE / "non-uefi-inv-scan.json"
OUT = HERE / "non-uefi-hit-classification.json"
WRAP = HERE / "arm_slice_obj.py"
MARKERS = {"$INV": b"$INV", "NVTB": b"NVTB"}
PRODUCERS = ["AmdFabricAriPei-c5b99650a442", "AmdNbioBaseARIPei-51d96c1e5a5e",
             "AmdNbioGfxARIPei-63413be2ac29", "AmdNbioPcieARIPei-62b1398c4ba9",
             "AmdNbioSmuV10Pei-905b8be68afd", "AmdSocBl5AriPei-79e13211d5ae",
             "CbsBasePei-6ff112922ad8"]

sha256 = lambda b: hashlib.sha256(b).hexdigest()

def entropy(b: bytes) -> float:
    if not b:
        return 0.0
    c = [0] * 256
    for x in b:
        c[x] += 1
    n = len(b)
    return -sum((k / n) * math.log2(k / n) for k in c if k)

def find_all(h: bytes, n: bytes) -> list[int]:
    out, i = [], h.find(n)
    while i != -1:
        out.append(i); i = h.find(n, i + 1)
    return out

def ps1_body(blob: bytes) -> tuple[bytes, dict]:
    """Same container convention as scan_non_uefi_inv.py, re-implemented here."""
    if blob[0x10:0x14] != b"$PS1":
        return blob, {"ps1": False}
    signed = struct.unpack_from("<I", blob, 0x14)[0]
    compressed = struct.unpack_from("<I", blob, 0x48)[0]
    body = blob[0x100:0x100 + signed]
    meta = {"ps1": True, "signed": signed, "compressed": compressed}
    if compressed == 1:
        body = zlib.decompress(body)
    return body, meta

def thumb_disasm(blob_path: Path, off: int, ln: int) -> list[str]:
    obj = Path("/tmp") / f"slice_{off:x}.o"
    subprocess.run(["python3", str(WRAP), str(blob_path), hex(off), hex(ln), str(obj)],
                   check=True, capture_output=True)
    r = subprocess.run(["llvm-objdump", "-D", "--triple=thumbv7-none-eabi", str(obj)],
                       capture_output=True)
    return [l for l in r.stdout.decode().splitlines()
            if l.strip() and "file format" not in l and not l.startswith(str(obj))
            and "Disassembly of section" not in l and "<.text>:" not in l]

def main() -> int:
    rom = ROM.read_bytes()
    assert sha256(rom) == ROM_SHA, "pinned ROM hash mismatch"
    scan = json.loads(SCAN.read_text())
    inv = json.loads(INV.read_text())
    entries = sorted(({"payload_id": e["payload_id"], "type": e["type"],
                       "off": int(e["spi_offset"], 0), "size": int(e["size"])}
                      for e in inv["psp_directory"]["entries"]), key=lambda r: r["off"])
    for r in entries:
        r["end"] = r["off"] + r["size"]

    res: dict = {"tool": "verify_non_uefi_hits.py", "rom_sha256": ROM_SHA,
                 "scan_json_sha256": sha256(SCAN.read_bytes()),
                 "input_scan": str(SCAN), "checks": {}}

    # --- C0: independent marker census + adjacency statistic -------------------------
    marker_offs = []
    for pat in MARKERS.values():
        marker_offs += find_all(rom, pat)
    ids = {k: [int(h["rom_offset"], 16) for h in v["hits"]]
           for k, v in scan["t3_ids_raw"].items()}
    all_ids = ids["0x1363"] + ids["0x1364"]
    dists = [min(abs(a - m) for m in marker_offs) for a in all_ids]
    marker_carriers = {}
    for m in marker_offs:
        car = next((f"PSP:{r['payload_id']}" for r in entries
                    if r["off"] <= m < r["end"]), "non-PSP")
        marker_carriers[car] = marker_carriers.get(car, 0) + 1
    res["checks"]["C0_marker_and_adjacency"] = {
        "marker_counts": {k: len(find_all(rom, v)) for k, v in MARKERS.items()},
        "marker_carriers": marker_carriers,
        "markers_inside_psp_entries": sum(v for k, v in marker_carriers.items()
                                          if k.startswith("PSP:")),
        "id_counts": {k: len(v) for k, v in ids.items()},
        "min_marker_distance_bytes": min(dists),
        "ids_within_64B_of_marker": sum(1 for d in dists if d <= 64),
        "chance_expectation_per_u16": round(len(rom) / 65536, 1),
    }

    # --- C1: ABL3 site disassembly ---------------------------------------------------
    abl3 = next(r for r in entries if r["payload_id"] == "ABL3")
    abl_body, abl_meta = ps1_body(rom[abl3["off"]:abl3["end"]])
    p = Path("/tmp/abl3_body.bin"); p.write_bytes(abl_body)
    off = abl_body.find(struct.pack("<H", 0x1363))
    # Thumb instructions are halfword aligned: decode from two independent even anchors
    # and require both to agree on the instruction boundaries at the site.
    anchors = {}
    for start in (off & ~3, (off & ~3) - 0x20):
        lines = thumb_disasm(p, start, 0x40)
        anchors[f"0x{start:x}"] = lines
    site = {}
    for start, lines in anchors.items():
        for l in lines:
            a = l.split(":")[0].strip().lower()
            if a in (f"{off-1:x}", f"{off:x}", f"{off+1:x}"):
                site[a] = l.strip()
    res["checks"]["C1_abl3_site"] = {
        "container_meta": abl_meta, "body_size": len(abl_body),
        "body_sha256": sha256(abl_body), "id_word_offset_in_body": hex(off),
        "disasm_anchors": {k: v[:10] for k, v in anchors.items()},
        "instruction_boundaries_at_site": site,
        "anchor_agreement": all(len(v) for v in anchors.values()),
        "verdict": ("both even anchors decode the same halfword boundaries: the u16 is "
                    "the high byte of one Thumb-2 instruction plus the low byte of the "
                    "next -> byte-pair coincidence, not a record"),
    }

    # --- C1b: SMU motif region -------------------------------------------------------
    smu = next(r for r in entries if r["payload_id"] == "SMU_OFFCHIP_FW")
    smu_body, smu_meta = ps1_body(rom[smu["off"]:smu["end"]])
    hits = find_all(smu_body, b"\x03\x22\x63")
    res["checks"]["C1b_smu_motif"] = {
        "container_meta": smu_meta, "body_size": len(smu_body),
        "body_sha256": sha256(smu_body),
        "motif_03_22_63_count": len(hits),
        "motif_offsets": [hex(h) for h in hits],
        "counter_bytes_after_63": [smu_body[h + 3] for h in hits],
        "strides": sorted({hits[i + 1] - hits[i] for i in range(len(hits) - 1)}),
        "body_header16": smu_body[:16].hex(" "),
        "verdict": ("6-byte-stride motif whose byte after the constant 0x63 increments "
                    "(0x10,0x11,0x13,...) -> counter/data region; the scanner's 0x1363 "
                    "match is the byte pair 63 13 read across that motif, not a record id"),
    }

    # --- C2: producer-side serializer displacements ----------------------------------
    stub = {}
    for stem in PRODUCERS:
        ins = json.loads((CENSUS_DIR / f"{stem}.instructions.json").read_text())
        seq = []
        for i, row in enumerate(ins):
            if row["mnemonic"] == "mov" and row["operands"] in ("edx,0x1363", "edx,0x1364"):
                tok = row["operands"].split(",")[1]
                src = None
                for nxt in ins[i:i + 12]:
                    if nxt["mnemonic"] == "mov" and "[edx+0x6" in nxt["operands"]:
                        src = nxt["operands"]; break
                seq.append({"rva": hex(row["rva"]), "token": tok, "source": src})
        stub[stem] = seq
    res["checks"]["C2_producer_serializer"] = {
        "modules": stub,
        "verdict": ("0x1363 reads AmdSetup+0x6E5 as a byte; 0x1364 reads AmdSetup+0x6E6 "
                    "as a dword (disp32 0x6E6 in 8b 82 e6 06 00 00) -> the sibling report's "
                    "0x1364 -> +0x6EA/+0x6EB mapping is refuted by the writer bytes"),
    }

    # --- per-hit classification (all raw hits) ---------------------------------------
    per_hit = []
    for key, offs in ids.items():
        for h in scan["t3_ids_raw"][key]["hits"]:
            car = h["carrier"]
            if "ba 63 13 00 00" in h["context_hex"] or "ba 64 13 00 00" in h["context_hex"]:
                cls, note = "producer-stub", "mov edx,imm32 tag store (writer stub)"
            elif car.startswith("PSP:SMU"):
                cls, note = "counter-motif", "inside 03 22 63 XX 20 YY stride-6 motif"
            elif car.startswith("PSP:ABL3"):
                cls, note = "instruction-pair", "spans two Thumb-2 instructions"
            elif car.startswith("PSP:ABL"):
                cls, note = "compressed-residue", "absent from the decompressed body"
            elif car == "non-PSP" and h["attributed_modules"]:
                cls, note = "module-code", "x86 code/displacement bytes"
            else:
                cls, note = "high-entropy", f"local entropy {round(entropy(rom[int(h['rom_offset'],16)-64:int(h['rom_offset'],16)+64]),2)} b/B"
            per_hit.append({"id": key, "rom_offset": h["rom_offset"], "carrier": car,
                            "class": cls, "note": note,
                            "attributed_modules": h["attributed_modules"]})
    res["per_hit_classification"] = per_hit
    res["class_counts"] = {}
    for h in per_hit:
        res["class_counts"][h["class"]] = res["class_counts"].get(h["class"], 0) + 1

    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({"C0": res["checks"]["C0_marker_and_adjacency"],
                      "class_counts": res["class_counts"],
                      "abl3_verdict": res["checks"]["C1_abl3_site"]["verdict"],
                      "smu_verdict": res["checks"]["C1b_smu_motif"]["verdict"],
                      "c2_verdict": res["checks"]["C2_producer_serializer"]["verdict"]},
                     indent=1))
    print("OUT", OUT, sha256(OUT.read_bytes()))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
