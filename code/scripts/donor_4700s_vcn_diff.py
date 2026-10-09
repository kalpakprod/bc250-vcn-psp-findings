#!/usr/bin/env python3
"""4700S vs BC250 5.00 CLV: what does a WORKING VCN platform do differently?

Read-only. Parses both PSP directories, diffs the type sets, extracts both SMU
firmware blobs and scans them for VCN/power markers, diffs the APCB DFG words,
and scans both full images for the BC250 glitch-signed donor unlock values.
Evidence: evidence/firmware-audit/20260923-donor-4700s-vcn/diff-result.json
"""

import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from firmware_audit import parse_psp  # project-proven parser

ROOT = Path(__file__).resolve().parent.parent
IMG4700 = (
    ROOT
    / "archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/4700S/C0A/C0A"
)
IMGBC = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
EVID = ROOT / "evidence/firmware-audit/20260923-donor-4700s-vcn"

SHA4700 = "bb2cf51df4099a4c4a01c9959c13cfa186f5e59abd2eb04de731670febca8243"
SHABC = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"

MARKERS = [
    b"VCN",
    b"Vcn",
    b"vcn",
    b"PowerUp",
    b"PowerDown",
    b"Dpm",
    b"DPM",
    b"POWERUP",
    b"PowerUpVcn",
    b"smu",
    b"SMU",
    b"gfx",
    b"Gfx",
]


def parse_psp_dir(img: bytes, dir_off: int) -> dict:
    parsed = parse_psp(img, dir_off)
    assert parsed, f"no valid $PSP dir at {hex(dir_off)}"
    entries = []
    for e in parsed["entries"]:
        body = img[e["spi_offset"] : e["spi_offset"] + e["size"]]
        entries.append(
            {
                "index": e["index"],
                "type": hex(e["type"]),
                "subprogram": e["subprogram"],
                "flags": hex(e["flags"]),
                "size": e["size"],
                "spi_offset": hex(e["spi_offset"]),
                "body_sha256": hashlib.sha256(body).hexdigest()[:16],
            }
        )
    return {"dir_offset": hex(dir_off), "count": len(entries), "entries": entries}


def scan_markers(blob: bytes) -> dict:
    out = {}
    for m in MARKERS:
        hits = []
        start = 0
        while True:
            i = blob.find(m, start)
            if i < 0:
                break
            hits.append(hex(i))
            start = i + 1
            if len(hits) >= 8:
                break
        if hits:
            out[m.decode()] = hits
    return out


def apcb_groups(img: bytes, base: int, size: int) -> dict:
    g = {}
    off = base + 0x20  # skip APCB header (tokens header)
    end = base + size
    while off + 8 <= end:
        sig = img[off : off + 4]
        if sig in (b"UNKN", b"PSPG", b"DFG ", b"MEMG", b"FCHG", b"CBSG"):
            gid, flags, inst, sz = struct.unpack_from("<HBBH", img, off + 4)
            g[sig.decode().strip()] = {
                "offset": hex(off - base),
                "gid": gid,
                "size": sz,
                "body": img[off : off + sz],
            }
            off += sz
        else:
            off += 4
    return g


def main() -> int:
    i47 = IMG4700.read_bytes()
    ibc = IMGBC.read_bytes()
    assert hashlib.sha256(i47).hexdigest() == SHA4700
    assert hashlib.sha256(ibc).hexdigest() == SHABC

    d47 = parse_psp_dir(i47, 9306112)  # from 20260914-4700s/inventory.json
    dbc = parse_psp_dir(ibc, 0x8E0000)
    t47 = {e["type"] for e in d47["entries"]}
    tbc = {e["type"] for e in dbc["entries"]}

    # SMU blobs: biggest entry that is not the biggest-but-ABL (type 0x30+ are ABLs)
    smu47 = next(e for e in d47["entries"] if e["type"] == "0x8")
    smubc = next((e for e in dbc["entries"] if e["type"] == "0x8"), None)
    b47 = i47[int(smu47["spi_offset"], 16) :][: smu47["size"]]

    # donor unlock values from the BC250 glitch-signed build
    needles = {
        "0x2544C382": b"\x82\xc3\x44\x25",
        "0x00107FF": b"\xff\x07\x01\x00",
        "0x0010FFF": b"\xff\x0f\x01\x00",
    }
    value_hits = {}
    for name, img in (("4700S", i47), ("BC250_clv", ibc)):
        value_hits[name] = {
            n: [
                hex(m.start())
                for m in __import__("re").finditer(__import__("re").escape(v), img)
            ]
            for n, v in needles.items()
        }

    apcb47 = apcb_groups(i47, 11210752, 1160)
    apcbbc = apcb_groups(ibc, 0xAB1000, 0xB9C)
    dfg = {}
    for name, ag in (("4700S", apcb47), ("BC250_clv", apcbbc)):
        if "DFG" in ag:
            body = ag["DFG"]["body"]
            dfg[name] = {
                hex(o): hex(struct.unpack_from("<I", body, o)[0])
                for o in (0x130, 0x16C)
                if o + 4 <= len(body)
            }

    out = {
        "scope": "read-only diff of donor 4700S (working VCN lineage) vs BC250 5.00 CLV",
        "images": {"4700S": SHA4700, "BC250_clv": SHABC},
        "psp_dir": {"4700S": d47, "BC250_clv": dbc},
        "type_diff": {
            "only_in_4700S": sorted(t47 - tbc),
            "only_in_BC250": sorted(tbc - t47),
            "common": sorted(t47 & tbc),
        },
        "smu_fw": {
            "4700S": {**smu47, "markers": scan_markers(b47)},
            "BC250_clv": (smubc or {}).get(
                "body_sha256", "entry not type 0x8 in CLV dir"
            ),
        },
        "dfg_words": dfg,
        "donor_value_hits": value_hits,
    }
    EVID.mkdir(parents=True, exist_ok=True)
    (EVID / "diff-result.json").write_text(json.dumps(out, indent=2) + "\n")

    print("PSP types only in 4700S:", out["type_diff"]["only_in_4700S"])
    print("PSP types only in BC250:", out["type_diff"]["only_in_BC250"])
    print("4700S SMU fw:", smu47["size"], "B @", smu47["spi_offset"])
    print("4700S SMU markers:", json.dumps(out["smu_fw"]["4700S"]["markers"], indent=1))
    print("DFG words:", json.dumps(dfg, indent=1))
    for name in value_hits:
        print(
            f"donor values in {name}:", {k: len(v) for k, v in value_hits[name].items()}
        )
    return 0


if __name__ == "__main__":
    main()
