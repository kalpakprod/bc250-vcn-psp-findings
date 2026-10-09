#!/usr/bin/env python3
import hashlib, json, struct
from pathlib import Path
p = Path("/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin")
b = p.read_bytes()
u32 = lambda off: struct.unpack_from("<I", b, off)[0]
fields = {
    "raw_size": len(b),
    "raw_sha256": hashlib.sha256(b).hexdigest(),
    "table_literal_at_rva_0x1b1c": hex(u32(0x1b1c)),
    "table_row0_plus4_at_rva_0x170cc": hex(u32(0x170cc)),
    "table_row0_plus0c_at_rva_0x170d4": hex(u32(0x170d4)),
    "table_row1_plus4_at_rva_0x170e8": hex(u32(0x170e8)),
    "table_row0_plus8_not_used_by_this_loop": hex(u32(0x170d0)),
}
expected = {
    "raw_size": 94624,
    "raw_sha256": "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a",
    "table_literal_at_rva_0x1b1c": "0x6e1c8",
    "table_row0_plus4_at_rva_0x170cc": "0x5e479",
    "table_row0_plus0c_at_rva_0x170d4": "0x6e154",
    "table_row1_plus4_at_rva_0x170e8": "0x0",
    "table_row0_plus8_not_used_by_this_loop": "0x62059",
}
result = {"status": "PASS" if fields == expected else "FAIL",
          "checks": {"passed": sum(fields[k] == v for k,v in expected.items()),
                     "total": len(expected)},
          "fields": fields}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
raise SystemExit(0 if result["status"] == "PASS" else 1)
