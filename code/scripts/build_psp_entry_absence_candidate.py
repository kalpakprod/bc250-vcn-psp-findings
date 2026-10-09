#!/usr/bin/env python3
"""Build the $PSP entry-absence candidate for BC-250 (lane D).

Question: what does the PSP do when the two VCN-lock carriers (type 0x24
SEC_GASKET, type 0x45 TOS_SECURITY_POLICY) are REMOVED from the $PSP directory
entirely? Never tested: D3/D3-B2 tested modified/stale-signed carriers, not
absence (plan vcn-verifier-first, 2026-09-23).

Transformation, one-variable discipline:
  1. base = BC250_5.00_clv.bin (stock, hash recorded), read-only.
  2. entries 0x24 and 0x45 in the $PSP directory are replaced with the image's
     own empty-entry convention (16 bytes of 0xFF, as in trailing slots).
  3. fletcher32 over the directory is refreshed with the exact geometry the
     existing builders use (scripts/build_glitch_unlock_candidate.py).
  4. nothing else changes: bodies stay in place (unreferenced), all other
     entries keep their bytes.

The output is a static candidate. No flash, no hardware action, no claim about
board behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

PSP_DIR = 0x8E0000
EMPTY_ENTRY = b"\xff" * 16
LOCK_TYPES = (0x24, 0x45)


def fletcher32(data: bytes) -> int:
    if len(data) % 2:
        data += b"\0"
    s1 = s2 = 0
    for off in range(0, len(data), 2):
        word = data[off] | (data[off + 1] << 8)
        s1 = (s1 + word) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def dir_count(rom: bytes) -> int:
    return struct.unpack_from("<I", rom, PSP_DIR + 8)[0]


def dir_fletcher_span(count: int) -> bytes:
    end = PSP_DIR + 0x10 + 16 * count
    return None, end  # replaced below; kept for clarity of geometry


def remove_entry(rom: bytearray, ptype: int) -> dict:
    count = dir_count(rom)
    for i in range(count):
        o = PSP_DIR + 0x10 + i * 0x10
        if rom[o] == ptype:
            was = (
                struct.unpack_from("<I", rom, o + 4)[0],
                struct.unpack_from("<I", rom, o + 8)[0],
            )
            rom[o : o + 16] = EMPTY_ENTRY
            return {"index": i, "was_size": was[0], "was_location": hex(was[1])}
    raise SystemExit(f"PSP entry type 0x{ptype:02X} not found")


def refresh_dir_fletcher(rom: bytearray) -> dict:
    count = dir_count(rom)
    end = PSP_DIR + 0x10 + 16 * count
    was = struct.unpack_from("<I", rom, PSP_DIR + 4)[0]
    new = fletcher32(bytes(rom[PSP_DIR + 8 : end]))
    struct.pack_into("<I", rom, PSP_DIR + 4, new)
    return {"was": hex(was), "now": hex(new), "span": [hex(PSP_DIR + 8), hex(end)]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    base_bytes = args.base.read_bytes()
    rom = bytearray(base_bytes)
    base_sha = hashlib.sha256(base_bytes).hexdigest()

    removed = {f"0x{t:02X}": remove_entry(rom, t) for t in LOCK_TYPES}
    flet = refresh_dir_fletcher(rom)

    out_sha = hashlib.sha256(rom).hexdigest()
    diff = [i for i in range(len(rom)) if rom[i] != base_bytes[i]]

    # ---- self-checks -------------------------------------------------------
    checks: dict[str, object] = {}

    # 1. lock entries are gone from the directory.
    count = dir_count(rom)
    types_left = sorted(
        rom[PSP_DIR + 0x10 + 16 * i]
        for i in range(count)
        if rom[PSP_DIR + 0x10 + 16 * i] != 0xFF
    )
    checks["lock_types_absent"] = all(t not in LOCK_TYPES for t in types_left)
    checks["remaining_entry_count"] = len(types_left)

    # 2. stored fletcher32 equals the recomputed one on the candidate bytes.
    stored = struct.unpack_from("<I", rom, PSP_DIR + 4)[0]
    end = PSP_DIR + 0x10 + 16 * count
    checks["fletcher_ok"] = stored == fletcher32(bytes(rom[PSP_DIR + 8 : end]))

    # 3. every change is confined to the directory table + checksum word.
    lo = PSP_DIR + 4
    hi = PSP_DIR + 0x10 + 16 * count
    checks["diff_confinement"] = bool(diff) and all(lo <= i < hi for i in diff)
    checks["changed_bytes"] = len(diff)

    ok = all(
        v
        for k, v in checks.items()
        if k not in ("changed_bytes", "remaining_entry_count")
    )
    report = {
        "base": str(args.base),
        "base_sha256": base_sha,
        "out": str(args.out),
        "out_sha256": out_sha,
        "removed_entries": removed,
        "fletcher": flet,
        "checks": checks,
        "gate": "PASS" if ok else "FAIL",
        "claim_boundary": "static candidate only; PSP boot behavior UNRUN; no flash",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(bytes(rom))

    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
