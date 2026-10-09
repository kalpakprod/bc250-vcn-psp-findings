#!/usr/bin/env python3
"""Build the FCLK-1800 APCB candidate on the clean clv 5.00 base.

One variable per flash: this image changes ONLY the FCLK override record
inside APCB (the u16 the ABL1 token reader 0x1FB4 fetches via the
0x015F-gate / 0x0160-value pair) plus the one APCB checksum byte.

Mechanism evidence (all static/emulator, none hardware):
- The record: ROM 0xAB1B99 = gate byte 0x01, 0xAB1B9A..0xAB1B9B = u16 LE
  0x058C (1420) in the clean clv base (observed this session).
- The reader: ABL1 0x463C builds {0x015F, 0x0160, 0} and calls 0x1FB4;
  the gate token must answer non-zero or the value token is not queried
  (20260920-clv-abl1-fclk-uclk-branch-xhigh, A3 emulator checkpoint:
  gate missing/0 stops).
- The effect: A3 Unicorn checkpoint on the native ABL1 code with the real
  clean APCB bytes: ROM gate=1 + value=1420 -> FCLK service arg 1420; an
  in-memory changed word (1430) with the recomputed checksum -> arg 1430;
  FFFF -> rejection; gate off -> the 1200 default instead
  (.procoder/plans/clv500-overclock-result.md lines 104/108,
  docs/research/2026-09-23-abl-pll-service-boundary.md).
- VALIDATED (2026-09-24, after the first build): the actual candidate
  bytes run through the preserved native ABL1 harness
  (evidence/firmware-audit/20260923-abl95fc-next/emulate_pll_apcb_v001.py,
  Unicorn 2.1.4): control 1420, candidate -> FCLK service argument 1800,
  gate forced 0 -> 1200 with token 0x160 not queried. See
  emulation-apcb-v001-result.json. Still open: SVC28 transport to
  physical FCLK and the loader copy of APCB to runtime 0x7B000.

No NVRAM/AmdSetup bytes are touched (+0x703/+0x704 stay Manual/1420 as
persisted requests; the APCB record is the boot-read source). No PSP
entry table, $PS1, or signed-region changes: the APCB blob is
checksummed config data, and only its value+checksum bytes move.

Self-validation: APCB magic/size/checksum re-parse on the output, the
changed set must be exactly {0xAB1B9A, 0xAB1B9B, 0xAB1010}, everything
else byte-identical to the base. Exits nonzero on any failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

APCB_OFFSET = 0xAB1000
FCLK_GATE_OFF = 0xAB1B99  # gate byte (token 0x015F source), stays 0x01
FCLK_VALUE_OFF = 0xAB1B9A  # u16 LE (token 0x0160 source)
CHK_OFF = 0xAB1010  # APCB checksum byte (whole-blob)


def apcb_checksum(data: bytes, offset: int = APCB_OFFSET) -> int:
    """The APCB checksum: negate the sum of the whole blob with the
    checksum byte itself excluded (matches scripts/apcb_detail.py)."""
    size = struct.unpack_from("<I", data, offset + 8)[0]
    total = sum(data[offset : offset + size]) - data[offset + 0x10]
    return (-total) & 0xFF


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--fclk", type=int, default=1800)
    a = ap.parse_args()

    base = a.base.read_bytes()
    if len(base) != 0x1000000:
        print(f"base size {len(base):#x} != 0x1000000", file=sys.stderr)
        return 1
    if base[APCB_OFFSET : APCB_OFFSET + 4] != b"APCB":
        print("APCB magic not found at 0xAB1000", file=sys.stderr)
        return 1

    # sanity of the record we are about to patch
    gate = base[FCLK_GATE_OFF]
    value = struct.unpack_from("<H", base, FCLK_VALUE_OFF)[0]
    apcb_size = struct.unpack_from("<I", base, APCB_OFFSET + 8)[0]
    stored_chk = base[CHK_OFF]
    calc_chk = apcb_checksum(base)
    print(
        f"base: APCB size 0x{apcb_size:X} gate={gate:#x} value={value} "
        f"chk stored={stored_chk:#04x} calc={calc_chk:#04x}"
    )
    if gate != 0x01:
        print(f"unexpected gate byte {gate:#x} (expected 0x01)", file=sys.stderr)
        return 1
    if value != 1420:
        print(f"unexpected base FCLK value {value} (expected 1420)", file=sys.stderr)
        return 1
    if stored_chk != calc_chk:
        print("base APCB checksum mismatch before patch", file=sys.stderr)
        return 1
    if not (0 < a.fclk <= 0x7FFF):
        print(f"fclk {a.fclk} out of u15 range", file=sys.stderr)
        return 1

    out = bytearray(base)
    struct.pack_into("<H", out, FCLK_VALUE_OFF, a.fclk)
    out[CHK_OFF] = apcb_checksum(bytes(out))

    # verify: re-parse the patched APCB
    if bytes(out[APCB_OFFSET : APCB_OFFSET + 4]) != b"APCB":
        print("output APCB magic lost", file=sys.stderr)
        return 1
    if out[CHK_OFF] != apcb_checksum(bytes(out)):
        print("output APCB checksum does not verify", file=sys.stderr)
        return 1
    new_value = struct.unpack_from("<H", out, FCLK_VALUE_OFF)[0]
    if new_value != a.fclk:
        print("value patch did not land", file=sys.stderr)
        return 1

    # verify: the changed set is exactly the three bytes
    changed = [i for i in range(len(base)) if out[i] != base[i]]
    expected = sorted([FCLK_VALUE_OFF, FCLK_VALUE_OFF + 1, CHK_OFF])
    if changed != expected:
        print(
            f"changed set {['%#x' % c for c in changed]} != expected "
            f"{['%#x' % c for c in expected]}",
            file=sys.stderr,
        )
        return 1

    a.output.write_bytes(bytes(out))
    sha = hashlib.sha256(bytes(out)).hexdigest()
    manifest = {
        "candidate": str(a.output),
        "base": {"path": str(a.base), "sha256": hashlib.sha256(base).hexdigest()},
        "patch": {
            "kind": "APCB FCLK override record (token 0x0160 value, gate 0x015F untouched)",
            "gate_offset": "0xAB1B99",
            "value_offset": "0xAB1B9A",
            "old_value": value,
            "new_value": a.fclk,
            "checksum_offset": "0xAB1010",
            "old_checksum": stored_chk,
            "new_checksum": out[CHK_OFF],
        },
        "changed_bytes": ["%#x" % c for c in changed],
        "output_sha256": sha,
        "evidence": [
            ".procoder/plans/clv500-overclock-result.md (A3 emulator checkpoints, lines 104/108)",
            "docs/research/2026-09-23-abl-pll-service-boundary.md",
            "docs/guides/bc250-clv500-memory-1-1-1-instruction.md",
        ],
        "open": [
            "1800 not emulator-run (the A3 checkpoint validated 1420/1430/FFFF/default on the same path)",
            "no hardware test; physical FCLK effect unproven",
        ],
        "flashed": False,
    }
    a.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"output: {a.output} ({len(out)} bytes)")
    print(f"sha256: {sha}")
    print(f"changed: {['%#x' % c for c in changed]}")
    print(
        f"FCLK {value} -> {a.fclk}, checksum {stored_chk:#04x} -> {out[CHK_OFF]:#04x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
