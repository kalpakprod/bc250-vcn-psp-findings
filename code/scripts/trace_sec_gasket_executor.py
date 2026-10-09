#!/usr/bin/env python3
"""P1.5a — SEC_GASKET executor RE (offline, static analysis).

Planned since 2026-08-26, never built until 2026-09-25.

Inputs (evidence/psp-bodies-import/):
  - SEC_GASKET~0x24_B.51.0.16.body     (11344 B, PSP policy blob $PS1)
  - ABL1~0x31_21.11.26.0.body          (48336 B, ARM Thumb-2 executor)

Outputs (evidence/firmware-audit/20260925-sec-gasket-executor/):
  - executor-map.json — group→interpreter→SMN-address map, commit/lock sites
  - executor-report.md — human-readable trace

Key questions to answer (from docs/research/imported/bc250-bios-docs/01-psp-policy-chain.md):
  Q1: fn@0xfeac (интерпретатор group 0x280/0x281) — WHO calls it from OUTSIDE
      the container? Static bl/blx/b.w scans on the container showed ZERO.
  Q2: Where is the fabric translation-matrix LOCK enforced (LockDFReg 0x1b)?
      Is it a separate SMN write after group 0x280 apply, or a side-effect of
      a specific group 0x280 pair?
  Q3: What is the requester/client id used by fn@0xfeac's svc 0x7c calls?
      (Whitelisted for VCN bank 12?)

Method:
  1. Parse $PS1 header: magic @+0x10, size @+0x14, group table @+0x100.
     Enumerate groups with their (type, count, pairs).
  2. Cross-ref group types to ABL1 fn@ addresses per predecessor decode.
  3. In ABL1: locate call-sites to fn@0xfeac, fn@0x2178, fn@0x20d4, fn@0x1167c
     via Thumb-2 `bl` (11110* / 11111* imm11+imm11) and `blx` scans.
  4. Follow svc numbers (svc 0x7c = SMN write via 4-byte access) and their
     argument origins.
  5. Emit JSON graph.

Boundaries:
  - Static-only. No hardware, no writes.
  - Interpreter reconstructions use documented per-type behavior; assume
    unknown branches abort silently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

SEC_GASKET_PATH = Path("evidence/psp-bodies-import/SEC_GASKET~0x24_B.51.0.16.body")
ABL1_PATH = Path("evidence/psp-bodies-import/ABL1~0x31_21.11.26.0.body")
# Actual container of fn@0xfeac / fn@0x2178 / etc: the PSP TRUSTED OS body,
# as decoded in docs/research/imported/bc250-bios-docs/01-psp-policy-chain.md.
# Body layout: first 0x100 bytes = header (no code); Thumb-2 code starts @+0x100.
# So VA in the doc == body_off + 0x100 - 0x100 = body_off (with VA base 0 for code section).
# But actually addresses in the doc are already RELATIVE to code start (which is +0x100).
# So target address 0xfeac in doc == body offset 0xfeac + 0x100 = 0xffac.
PSP2_PATH = Path("evidence/psp-bodies-import/PSP_FW_TRUSTED_OS~0x2_0.1C.0.2.body")
PSP2_CODE_BASE = 0x100  # from 01-psp-policy-chain.md: "Thumb-2 code starts at +0x100"

# Known fn addresses in ABL1 from 01-psp-policy-chain.md
ABL1_FUNCS = {
    0x13468: ("loader $PS1", "svc 0x90/0x88/0x68; RSA verify via fn@0xd1fc"),
    0x1167C: ("group registry", "reads @0xE5CBDC[type] -> (count, pairs)"),
    0x2178: ("interp primary", "types 0x203/0x217 direct; else svc 0x7c(a,v,4)"),
    0xFEAC: (
        "interp 0x280-family",
        "0x281 direct; 0x280/0x282/0x284 svc 0x7c; else svc 0x7c(a,0,4)",
    ),
    0x20D4: ("sequencer", "types 0x201,0x205,0x203,0x20A,0x20B,0x210 in fixed order"),
    0x2008: (
        "wrapper (byte flag + special 0x225)",
        "gates fn@0x88fc == 0x100 -> fn@0x2178",
    ),
    0x1EF4: ("group 0x211 applier", "called from fn@0xca78"),
    0x2084: ("group 0x215 applier", ""),
    0xA4E4: ("donor set (0x206/0x210/0x208)", "RAM+0x41C gate + byte flag"),
    0x1EC4: ("10 fixed pairs applier by byte flag", ""),
    0xCAA4: ("group 0x214 applier", ""),
    0xCDBC: ("group 0x290 applier", ""),
    0xE1F6: ("group 0x221 applier", ""),
    0xEB8E: ("group 0x222 then 0x284", ""),
}

# arm dispatcher entrypoints from doc
DISPATCH_ENTRIES = {
    0xC0DA: 0x13468,  # loader
    0xC344: 0x20D4,  # sequencer
    0xC632: 0x1EF4,  # via fn@0xca78 -> 0x211
    0xC638: 0xCAA4,  # 0x214
    0xC2B0: 0x1EC4,  # via 0x20D0 trampoline
    0xBF6E: 0xA4E4,  # donor via fn@0x946c
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_ps1(blob: bytes) -> dict:
    """Parse SEC_GASKET body (no $PS1 header — stripped in this dump).

    Observed layout (verified against 02-gasket-groups.md counts 1230/31/13/100/31):
      +0x00: u32 group_count (0x05 = 5 groups here)
      +0x04..: header/preamble (16 bytes zeroed?), then group table
      Group table begins at +0x40 for BC-250 SEC_GASKET; observed at 0x40.
      Each group: u32 type, u32 entry_count, followed by entry_count*8 bytes
        (addr u32, value u32).
    """
    off = 0x40  # empirical from body scan
    groups = []
    while off + 8 <= len(blob):
        gtype, gcount = struct.unpack_from("<II", blob, off)
        if gtype not in (
            0x201,
            0x203,
            0x210,
            0x280,
            0x281,
            0x211,
            0x213,
            0x214,
            0x215,
            0x217,
            0x218,
            0x225,
            0x226,
            0x227,
            0x206,
            0x208,
            0x212,
            0x282,
            0x290,
            0x221,
            0x222,
            0x284,
        ):
            # not a group header — end of table
            break
        if gcount == 0 or gcount > 5000:
            break
        pairs_off = off + 8
        pairs = []
        for i in range(gcount):
            p = pairs_off + i * 8
            if p + 8 > len(blob):
                break
            addr, val = struct.unpack_from("<II", blob, p)
            pairs.append((addr, val))
        groups.append(
            {
                "type": f"0x{gtype:x}",
                "count": gcount,
                "pairs_parsed": len(pairs),
                "off": f"{off:#x}",
                "sample": [f"{a:#x}<-{v:#x}" for a, v in pairs[:6]],
            }
        )
        off = pairs_off + gcount * 8
    return {"table_start": "0x40", "group_count": len(groups), "groups": groups}


def scan_thumb2_bl(blob: bytes, target_addr: int, base: int = 0) -> list[int]:
    """Scan for Thumb-2 BL/BLX targeting `target_addr` (absolute, image base=0).

    Thumb-2 BL/BLX encoding (2×16-bit):
      hi = 11110 S imm10   (F0..F7 or F8..FB depending on S/imm10)
      lo = 11 J1 1 J2 imm11  (BL) or 11 J1 0 J2 imm11 (BLX)
      I1 = NOT(J1 XOR S), I2 = NOT(J2 XOR S)
      imm32 = SignExtend(S:I1:I2:imm10:imm11:'0', 32)
      target = PC + imm32 (PC = current + 4)

    Returns list of call-site addresses.
    """
    hits = []
    for off in range(0, len(blob) - 4, 2):
        hi, lo = struct.unpack_from("<HH", blob, off)
        if (hi & 0xF800) != 0xF000:
            continue
        # BL: (lo & 0xD000) == 0xD000; BLX: (lo & 0xD000) == 0xC000
        if (lo & 0xD000) != 0xD000 and (lo & 0xD000) != 0xC000:
            continue
        s = (hi >> 10) & 1
        imm10 = hi & 0x3FF
        j1 = (lo >> 13) & 1
        j2 = (lo >> 11) & 1
        imm11 = lo & 0x7FF
        i1 = 1 - (j1 ^ s)
        i2 = 1 - (j2 ^ s)
        imm = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
        if s:
            imm |= 0xFE000000  # sign-extend from bit 24
            imm = imm - (1 << 32) if imm & (1 << 31) else imm
        pc = base + off + 4
        target = (pc + imm) & 0xFFFFFFFF
        # BLX aligns to 4
        if (lo & 0xD000) == 0xC000:
            target = target & ~0x3
        # allow ±1 for thumb bit
        if (
            target == target_addr
            or target == (target_addr | 1)
            or target == (target_addr & ~1)
        ):
            hits.append(base + off)
    return hits


def scan_svc(blob: bytes) -> dict[int, list[int]]:
    """Scan Thumb-1 SVC (0xDFxx). Returns {svc_num: [offsets]}."""
    out: dict[int, list[int]] = {}
    for off in range(0, len(blob) - 2, 2):
        hi = blob[off + 1]
        lo = blob[off]
        if hi == 0xDF:
            out.setdefault(lo, []).append(off)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("evidence/firmware-audit/20260925-sec-gasket-executor"),
    )
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not SEC_GASKET_PATH.exists() or not ABL1_PATH.exists():
        print(f"[!] Missing inputs. Need:\n  {SEC_GASKET_PATH}\n  {ABL1_PATH}")
        return 2

    gasket = SEC_GASKET_PATH.read_bytes()
    abl1 = ABL1_PATH.read_bytes()
    psp2 = PSP2_PATH.read_bytes() if PSP2_PATH.exists() else None

    gasket_sha = sha256(gasket)
    abl1_sha = sha256(abl1)
    psp2_sha = sha256(psp2) if psp2 else "-"

    print(f"[*] SEC_GASKET  {len(gasket):#x} B  sha256={gasket_sha[:16]}...")
    print(f"[*] ABL1        {len(abl1):#x} B  sha256={abl1_sha[:16]}...")
    print(f"[*] PSP2 (TOS)  {len(psp2 or b''):#x} B  sha256={psp2_sha[:16]}...")

    ps1 = parse_ps1(gasket)
    print(f"[*] policy table_start={ps1['table_start']} groups={ps1['group_count']}")
    for g in ps1["groups"][:12]:
        print(
            f"      type={g['type']:>7} count={g['count']:>4} pairs_parsed={g['pairs_parsed']} off={g['off']}"
        )

    # scan PSP2 body (code base +0x100) for callers of the known fn addresses.
    # Address in the doc = file offset within the code section.
    # BL scanner: scan starts at code base, target = base + doc_addr.
    scan_targets = psp2 if psp2 else abl1
    scan_source = "PSP2" if psp2 else "ABL1"
    scan_base = PSP2_CODE_BASE if psp2 else 0
    print(
        f"[*] Scanning {scan_source} body for Thumb-2 BL to known fn addrs (base={scan_base:#x})"
    )

    call_sites = {}
    for addr, (name, note) in ABL1_FUNCS.items():
        target_abs = scan_base + addr
        # scanner works on the code-only slice starting at scan_base, using addresses
        # in the same coordinate system (i.e. we pass base=scan_base so PC calc uses it).
        hits = scan_thumb2_bl(scan_targets[scan_base:], addr, base=0)
        # translate back: hits are relative to scan_targets[scan_base:]
        hits_doc = [f"{h:#x}" for h in hits]
        call_sites[f"{addr:#x}"] = {
            "name": name,
            "note": note,
            "callers": hits_doc,
            "count": len(hits),
        }
        marker = (
            " <-- KEY" if addr in (0xFEAC, 0x2178, 0x20D4, 0x1167C) and hits else ""
        )
        print(f"[fn] {addr:#x} {name:<40} callers={len(hits)}{marker}")

    # scan SVCs in the code section
    svc = scan_svc(scan_targets[scan_base:] if psp2 else abl1)
    key_svcs = {
        f"0x{s:x}": len(v)
        for s, v in svc.items()
        if s in (0x68, 0x7C, 0x87, 0x88, 0x8B, 0x90, 0xA6, 0x8C)
    }
    print(f"[svc] key counts: {key_svcs}")

    # dispatcher entry callers (ARM entries -> Thumb funcs)
    disp = {}
    for arm_ep, thumb_target in DISPATCH_ENTRIES.items():
        disp[f"{arm_ep:#x}"] = {
            "target": f"{thumb_target:#x}",
            "target_name": ABL1_FUNCS.get(thumb_target, ("?", ""))[0],
        }

    report = {
        "inputs": {
            "sec_gasket": {
                "path": str(SEC_GASKET_PATH),
                "sha256": gasket_sha,
                "size": len(gasket),
            },
            "abl1": {"path": str(ABL1_PATH), "sha256": abl1_sha, "size": len(abl1)},
        },
        "ps1_groups": ps1,
        "abl1_call_sites": call_sites,
        "abl1_svc_key_counts": key_svcs,
        "arm_dispatcher_entries": disp,
        "notes": [
            "Q1: fn@0xfeac callers within ABL1 -- see call_sites entry.",
            "Q2: LockDFReg 0x1b enforcement site not yet mapped (pending svc 0x7c traceback).",
            "Q3: Requester/client id for VCN bank 12 -- pending arg trace of svc 0x7c call-sites.",
            "Interp fn@0xfeac static verdict from predecessor decode: no in-container callers.",
        ],
    }

    (args.out_dir / "executor-map.json").write_text(json.dumps(report, indent=2))
    print(f"[=] wrote {args.out_dir / 'executor-map.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
