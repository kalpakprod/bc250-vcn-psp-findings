#!/usr/bin/env python3
import hashlib, json, struct
from pathlib import Path
p = Path("/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin")
b = p.read_bytes()
u32 = lambda o: struct.unpack_from("<I", b, o)[0]
fields = {
    "raw_size": len(b),
    "raw_sha256": hashlib.sha256(b).hexdigest(),
    "literal_table_base_at_0x1bac": hex(u32(0x1bac)),
    "literal_count_pointer_at_0x1bb0": hex(u32(0x1bb0)),
    "count_byte_at_rva_0x17100": hex(b[0x17100]),
    "row0_plus4_at_rva_0x170cc": hex(u32(0x170cc)),
    "row0_plus8_at_rva_0x170d0": hex(u32(0x170d0)),
    "row1_plus8_at_rva_0x170ec": hex(u32(0x170ec)),
}
print(json.dumps(fields, sort_keys=True, separators=(",", ":")))
expected = {
    "raw_size": 94624,
    "raw_sha256": "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a",
    "literal_table_base_at_0x1bac": "0x6e1c8",
    "literal_count_pointer_at_0x1bb0": "0x6e200",
    "count_byte_at_rva_0x17100": "0x2",
    "row0_plus4_at_rva_0x170cc": "0x5e479",
    "row0_plus8_at_rva_0x170d0": "0x62059",
    "row1_plus8_at_rva_0x170ec": "0x0",
}
raise SystemExit(0 if fields == expected else 1)
