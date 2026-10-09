#!/usr/bin/env python3
"""Parse AMD PSP HARDWARE_IP_CONFIG / IP discovery data."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

TOTAL_TABLES = 6
IP_NAMES = {
    1: "MP1",
    2: "MP2",
    3: "THM",
    4: "SMUIO",
    5: "FUSE",
    6: "CLKA",
    10: "PWR",
    11: "GC",
    12: "VCN",
    24: "IOHC",
    34: "MMHUB",
    35: "ATHUB",
    42: "SDMA0",
    43: "SDMA1",
    70: "PCIE",
    108: "NBIF",
    128: "SYSTEMHUB",
    150: "UMC",
    255: "MP0",
}


def parse(data: bytes) -> dict[str, object]:
    signature, major, minor, checksum, binary_size = struct.unpack_from("<IHHHH", data, 0)
    tables = []
    for index in range(TOTAL_TABLES):
        offset, table_checksum, size, padding = struct.unpack_from("<HHHH", data, 12 + index * 8)
        tables.append(
            {
                "index": index,
                "offset": offset,
                "checksum": table_checksum,
                "size": size,
                "padding": padding,
            }
        )

    ip_table = tables[0]
    offset = ip_table["offset"]
    ip_signature, ip_version, ip_size, ip_id, num_dies = struct.unpack_from("<IHHIH", data, offset)
    die_infos = [struct.unpack_from("<HH", data, offset + 14 + index * 4) for index in range(16)]
    dies = []
    for die_id, die_offset in die_infos[:num_dies]:
        cursor = die_offset
        actual_die_id, num_ips = struct.unpack_from("<HH", data, cursor)
        cursor += 4
        ips = []
        for _ in range(num_ips):
            hw_id, instance, num_bases, ip_major, ip_minor, revision, flags = struct.unpack_from(
                "<HBBBBBB", data, cursor
            )
            cursor += 8
            bases = list(struct.unpack_from(f"<{num_bases}I", data, cursor))
            cursor += num_bases * 4
            ips.append(
                {
                    "hw_id": hw_id,
                    "name": IP_NAMES.get(hw_id, f"HWID_{hw_id}"),
                    "instance": instance,
                    "version": f"{ip_major}.{ip_minor}.{revision}",
                    "harvest": flags & 0x0F,
                    "reserved": flags >> 4,
                    "base_addresses": [f"0x{base:08x}" for base in bases],
                }
            )
        dies.append({"die_id": actual_die_id, "num_ips": num_ips, "ips": ips})

    return {
        "size": len(data),
        "binary": {
            "signature": f"0x{signature:08x}",
            "version": f"{major}.{minor}",
            "checksum": f"0x{checksum:04x}",
            "declared_size": binary_size,
        },
        "tables": tables,
        "ip_discovery": {
            "signature": f"0x{ip_signature:08x}",
            "version": ip_version,
            "size": ip_size,
            "id": f"0x{ip_id:08x}",
            "num_dies": num_dies,
            "dies": dies,
        },
    }


def main() -> int:
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    report = parse(source.read_bytes())
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"binary={report['binary']['version']} declared={report['binary']['declared_size']} "
        f"ip_version={report['ip_discovery']['version']} dies={report['ip_discovery']['num_dies']}"
    )
    for die in report["ip_discovery"]["dies"]:
        print(f"die={die['die_id']} ips={die['num_ips']}")
        for ip in die["ips"]:
            bases = ",".join(ip["base_addresses"])
            print(
                f"  {ip['name']:<10} hwid={ip['hw_id']:3d} inst={ip['instance']} "
                f"v={ip['version']} harvest={ip['harvest']} bases={bases}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
