#!/usr/bin/env python3
"""Scan extracted Robin3 PSP/ABL entries for VCN, NBIO and isolation clues."""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

LITERALS = {
    "VCN_FABRIC": 0x02403000,
    "FABRIC_FRAME": 0x02400000,
    "GC_FABRIC": 0x02402C00,
    "THM_FABRIC": 0x02400C00,
    "VCN_SEG0_DW": 0x00007800,
    "VCN_SEG1_DW": 0x00007E00,
    "UVD_PGFSM_MMIO": 0x0001F800,
    "UVD_REGFILE_MMIO": 0x0001E000,
    "DOM6_BLOCK": 0x0006D000,
    "BC250_DID": 0x000013FE,
}
KEYWORDS = re.compile(
    rb"VCN|UVD|VCE|JPEG|VIDEO|HARVEST|ISOLAT|CLAMP|GASKET|NBIO|NBIF|BIF|"
    rb"MMHUB|SMN|PSP|POWER.?GAT|SECUR|FIREWALL|ROUTE|DOORBELL|FABRIC|SYSHUB",
    re.I,
)


def ascii_strings(data: bytes, minimum: int = 4) -> list[tuple[int, str]]:
    regex = re.compile(rb"[\x20-\x7e]{%d,}" % minimum)
    return [(match.start(), match.group().decode("ascii", "replace")) for match in regex.finditer(data)]


def utf16_strings(data: bytes, minimum: int = 4) -> list[tuple[int, str]]:
    regex = re.compile(rb"(?:[\x20-\x7e]\x00){%d,}" % minimum)
    return [(match.start(), match.group()[::2].decode("ascii", "replace")) for match in regex.finditer(data)]


def main() -> None:
    root = Path(sys.argv[1])
    report = []
    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue
        data = path.read_bytes()
        literal_hits = {}
        for name, value in LITERALS.items():
            pattern = struct.pack("<I", value)
            offsets = [match.start() for match in re.finditer(re.escape(pattern), data)]
            if offsets:
                literal_hits[name] = [f"0x{offset:x}" for offset in offsets[:100]]
        strings = []
        for offset, text in ascii_strings(data) + utf16_strings(data):
            if KEYWORDS.search(text.encode("ascii", "replace")):
                strings.append({"offset": f"0x{offset:x}", "text": text[:500]})
        if literal_hits or strings:
            report.append({
                "file": path.name,
                "size": len(data),
                "literals": literal_hits,
                "strings": strings[:200],
            })
    output = Path(sys.argv[2])
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"files_with_hits={len(report)} output={output}")
    for item in report:
        print(f"{item['file']}: literals={list(item['literals'])} strings={len(item['strings'])}")


if __name__ == "__main__":
    main()
