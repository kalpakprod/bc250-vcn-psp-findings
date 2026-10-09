#!/usr/bin/env python3
"""Verify a fresh-baseline BC-250 D3-B2 combined VCN candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

IMAGE_SIZE = 0x1000000
DIR, BHD, APCB = 0x8E0000, 0xAB0000, 0xAB1000
G_NEW, G_SIZE = 0x9E0000, 0x3010
P_NEW, P_SIZE = 0x9E4000, 0x708
EXPECTED_TAIL = [
    (0x0900C234, 0),
    (0x0900C914, 0),
    (0x0900C930, 0),
    (0x0900CB80, 0),
    (0x0900C234, 1),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fletcher32(data: bytes) -> int:
    s1 = s2 = 0
    for offset in range(0, len(data), 2):
        word = data[offset] | (data[offset + 1] << 8)
        s1 = (s1 + word) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def walk(body: bytes) -> tuple[list[tuple[int, list[tuple[int, int]]]], int]:
    groups: list[tuple[int, list[tuple[int, int]]]] = []
    offset = 0x40
    while offset + 8 <= len(body):
        group_type, count = struct.unpack_from("<II", body, offset)
        if group_type == 0 or group_type > 0xFFFF or count > 0x100000:
            break
        end = offset + 8 + count * 8
        if end > len(body):
            break
        pairs = [struct.unpack_from("<II", body, offset + 8 + index * 8) for index in range(count)]
        groups.append((group_type, pairs))
        offset = end
    return groups, offset


def values(groups: list[tuple[int, list[tuple[int, int]]]], address: int) -> list[int]:
    return [value for _, pairs in groups for current, value in pairs if current == address]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--apcb-mode", choices=("patched", "stock"), default="patched")
    args = parser.parse_args()
    source = args.source.resolve()
    candidate = args.candidate.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    stock = source.read_bytes()
    image = candidate.read_bytes()
    checks: dict[str, dict[str, object]] = {}

    def check(name: str, passed: bool, **details: object) -> None:
        checks[name] = {"pass": bool(passed), **details}

    check("sizes", len(stock) == len(image) == IMAGE_SIZE, source_size=len(stock), candidate_size=len(image))
    count = struct.unpack_from("<I", image, DIR + 8)[0]
    directory_end = DIR + 0x10 + count * 16
    stored_directory_checksum = struct.unpack_from("<I", image, DIR + 4)[0]
    check("psp_directory_fletcher32", count == 19 and stored_directory_checksum == fletcher32(image[DIR + 8 : directory_end]), count=count)
    bhd_count = struct.unpack_from("<I", image, BHD + 8)[0]
    bhd_end = BHD + 0x10 + bhd_count * 24
    check("bhd_fletcher32", struct.unpack_from("<I", image, BHD + 4)[0] == fletcher32(image[BHD + 8 : bhd_end]), count=bhd_count)

    entries: dict[int, tuple[int, int, int]] = {}
    for index in range(count):
        entry_type, size, location = struct.unpack_from("<IIQ", image, DIR + 0x10 + index * 16)
        entries[entry_type] = (index, size, location)
    check("directory_type_24", entries.get(0x24) == (7, G_SIZE, 0xFF9E0000), actual=entries.get(0x24))
    check("directory_type_45", entries.get(0x45) == (15, P_SIZE, 0xFF9E4000), actual=entries.get(0x45))

    gasket = image[G_NEW : G_NEW + G_SIZE]
    gasket_sizes = (struct.unpack_from("<Q", gasket, 0x14)[0], struct.unpack_from("<Q", gasket, 0x50)[0], struct.unpack_from("<I", gasket, 0x6C)[0])
    gasket_body = gasket[0x100 : 0x100 + 0x2E10]
    gasket_groups, gasket_end = walk(gasket_body)
    check("gasket_header", gasket[0x10:0x14] == b"$PS1" and gasket_sizes == (0x2E10, 0x2E10, G_SIZE), sizes=gasket_sizes)
    check("gasket_groups", [item[0] for item in gasket_groups] == [0x201, 0x203, 0x210, 0x280, 0x281] and [len(item[1]) for item in gasket_groups] == [1281, 31, 13, 105, 31] and gasket_end == 0x2E10)
    check("gasket_targets", values(gasket_groups, 0x03E810) == [6] and values(gasket_groups, 0x03A2011C) == [0x107FF, 0x107FF] and values(gasket_groups, 0x03A20124) == [0x10FFF])
    gasket_vcn = [(address, value) for _, pairs in gasket_groups for address, value in pairs if 0x0900C000 <= address <= 0x0900CFFF]
    check("gasket_vcn_bank", len(gasket_vcn) == 56, count=len(gasket_vcn))
    check("old_gasket_unchanged", image[0x982000 : 0x982000 + 0x2E50] == stock[0x982000 : 0x982000 + 0x2E50])
    stock_gasket = stock[0x982000 : 0x982000 + 0x2E50]
    check("gasket_signature_boundary", gasket[-0x100:] == stock_gasket[-0x100:] and gasket[:-0x100] != stock_gasket[:-0x100], signature_tail_preserved=True, signed_payload_changed=True)
    check("gasket_header_signature_material", gasket[0x00:0x10] == stock_gasket[0x00:0x10] and gasket[0xD0:0xF0] == stock_gasket[0xD0:0xF0])

    policy = image[P_NEW : P_NEW + P_SIZE]
    policy_sizes = (struct.unpack_from("<Q", policy, 0x14)[0], struct.unpack_from("<Q", policy, 0x50)[0], struct.unpack_from("<I", policy, 0x6C)[0])
    policy_body = policy[0x100 : 0x100 + 0x508]
    policy_groups, policy_end = walk(policy_body)
    check("policy_header", policy[0x10:0x14] == b"$PS1" and policy_sizes == (0x508, 0x508, P_SIZE), sizes=policy_sizes)
    check("policy_groups", [item[0] for item in policy_groups] == [0x210, 0x211, 0x280, 0x281] and [len(item[1]) for item in policy_groups] == [13, 0, 105, 31] and policy_end == 0x508)
    check("policy_targets", values(policy_groups, 0x03E810) == [6] and values(policy_groups, 0x03A2011C) == [0x107FF])
    policy_vcn = [(address, value) for _, pairs in policy_groups for address, value in pairs if 0x0900C000 <= address <= 0x0900CFFF]
    check("policy_vcn_tail", policy_vcn == EXPECTED_TAIL, actual=[[hex(a), hex(v)] for a, v in policy_vcn])
    check("old_policy_unchanged", image[0x9CA400 : 0x9CA400 + 0x6E0] == stock[0x9CA400 : 0x9CA400 + 0x6E0])
    stock_policy = stock[0x9CA400 : 0x9CA400 + 0x6E0]
    check("policy_signature_boundary", policy[-0x100:] == stock_policy[-0x100:] and policy[:-0x100] != stock_policy[:-0x100], signature_tail_preserved=True, signed_payload_changed=True)
    check("policy_header_signature_material", policy[0x00:0x10] == stock_policy[0x00:0x10] and policy[0xD0:0xF0] == stock_policy[0xD0:0xF0])
    stock_policy_body = stock_policy[0x100 : 0x100 + 0x4E0]
    insert_offset = 0x3E0
    policy_prefix_diff = [index for index in range(insert_offset) if policy_body[index] != stock_policy_body[index]]
    check("policy_exact_prefix_delta", policy_prefix_diff == [0x4C, 0xBC, 0x245, 0x246], offsets=[hex(index) for index in policy_prefix_diff])
    check("policy_shifted_group_281", policy_body[insert_offset + 40 :] == stock_policy_body[insert_offset:])

    apcb_size = struct.unpack_from("<I", image, APCB + 8)[0]
    calculated_apcb_checksum = (0x100 - sum(image[APCB + index] for index in range(apcb_size) if index != 0x10)) & 0xFF
    check("apcb_checksum", image[APCB + 0x10] == calculated_apcb_checksum, stored=image[APCB + 0x10], calculated=calculated_apcb_checksum)
    expected_word = bytes.fromhex("00ff7f00") if args.apcb_mode == "patched" else bytes.fromhex("00ff1f00")
    check("apcb_dfg_words", image[APCB + 0x130 : APCB + 0x134] == expected_word and image[APCB + 0x16C : APCB + 0x170] == expected_word, mode=args.apcb_mode)
    if args.apcb_mode == "stock":
        check("apcb_block_stock_identity", image[APCB : APCB + apcb_size] == stock[APCB : APCB + apcb_size])

    differences = [index for index, (a, b) in enumerate(zip(stock, image)) if a != b]
    allowed = lambda index: (
        0x8E0004 <= index < 0x8E0008
        or 0x8E0080 <= index < 0x8E0090
        or 0x8E0100 <= index < 0x8E0110
        or 0x9E0000 <= index < 0x9E4708
        or index in (0xAB1010, 0xAB1132, 0xAB116E)
    )
    outside = [index for index in differences if not allowed(index)]
    check("diff_confinement", not outside, changed_bytes=len(differences), outside=[hex(index) for index in outside[:16]])
    check("post_blob_erased_region", all(value == 0xFF for value in image[0x9E4708:0xAB0000]))

    passed = sum(bool(item["pass"]) for item in checks.values())
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/verify_vcn_d3b2_candidate.py",
        "source": {"path": str(source), "sha256": sha256(stock)},
        "candidate": {"path": str(candidate), "sha256": sha256(image)},
        "checks": checks,
        "passed_checks": passed,
        "total_checks": len(checks),
        "all_checks_pass": passed == len(checks),
        "signature_acceptance": "unverified; modified signed-payload bytes retain historical signature tails",
        "hardware_status": "unrun",
        "apcb_mode": args.apcb_mode,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "passed_checks": passed, "total_checks": len(checks), "all_checks_pass": result["all_checks_pass"]}))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
