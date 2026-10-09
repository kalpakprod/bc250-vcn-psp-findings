#!/usr/bin/env python3
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
RAW = ROOT / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
ELF = ROOT / "evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o"
LISTING = ROOT / "evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/xref-1b24-1b90.stdout"
STATUS = ROOT / "evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/xref-1b24-1b90.exit"
STDERR = ROOT / "evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/xref-1b24-1b90.stderr"
EXPECTED_RAW = "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
EXPECTED_ELF = "adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6"

raw = RAW.read_bytes()
listing_bytes = LISTING.read_bytes()
listing = listing_bytes.decode("utf-8")
def u32(off):
    return struct.unpack_from("<I", raw, off)[0]
def u8(off):
    return raw[off]
def line_at(addr):
    for line in listing.splitlines():
        m = re.match(r"\s*([0-9a-fA-F]+):\s+.*", line)
        if m and int(m.group(1), 16) == addr:
            parts = line.split("\t")
            return re.sub(r"\s+", " ", parts[-1].strip()).lower()
    return ""
checks = {}
checks["raw_sha256"] = hashlib.sha256(raw).hexdigest() == EXPECTED_RAW
checks["elf_sha256"] = hashlib.sha256(ELF.read_bytes()).hexdigest() == EXPECTED_ELF
checks["listing_exit_zero"] = STATUS.read_text().strip() == "0"
checks["listing_stderr_empty"] = STDERR.read_bytes() == b""
checks["listing_contains_rsb"] = "rsb r0, r4, r4, lsl #3" in line_at(0x1B48)
checks["listing_contains_add"] = "add.w r0, r6, r0, lsl #2" in line_at(0x1B4C)
checks["listing_loads_record_plus_8"] = "ldr r1, [r0, #0x8]" in line_at(0x1B50)
checks["listing_loads_count_byte"] = "ldrb r0, [r7]" in line_at(0x1B5C)
loop_lines = []
for line in listing.splitlines():
    m = re.match(r"\s*([0-9a-fA-F]+):\s+.*", line)
    if m and 0x1B48 <= int(m.group(1), 16) < 0x1B62:
        loop_lines.append(line.lower())
record_mem = [re.sub(r"\s+", " ", l.split("\t")[-1].strip()).lower()
              for l in loop_lines if "[r0" in l]
checks["only_record_member_load_is_plus_8"] = record_mem == ["ldr r1, [r0, #0x8]"]
checks["literal_table_base"] = u32(0x1BAC) == 0x6E1C8
checks["literal_count_pointer"] = u32(0x1BB0) == 0x6E200
candidate_base = 0x57100
table_va = u32(0x1BAC)
table_rva = table_va - candidate_base
stride = ((1 << 3) - 1) << 2
checks["computed_stride_is_0x1c"] = stride == 0x1C
checks["conditional_table_rva"] = table_rva == 0x170C8
checks["count_byte_is_two"] = u8(0x17100) == 2
checks["row0_plus4_is_candidate"] = u32(table_rva + 4) == 0x5E479
checks["row0_plus8_is_loaded_callback"] = u32(table_rva + 8) == 0x62059
row1_plus8 = table_rva + stride + 8
checks["row1_plus8_correct_offset"] = row1_plus8 == 0x170EC
checks["row1_plus8_zero"] = u32(row1_plus8) == 0
result = {
    "status": "PASS" if all(checks.values()) else "FAIL",
    "checks": {"total": len(checks), "passed": sum(checks.values()), "failed": sum(not v for v in checks.values())},
    "input": {"raw_path": str(RAW), "raw_sha256": hashlib.sha256(raw).hexdigest(),
              "elf_path": str(ELF), "elf_sha256": hashlib.sha256(ELF.read_bytes()).hexdigest(),
              "listing_path": str(LISTING), "listing_sha256": hashlib.sha256(listing_bytes).hexdigest()},
    "reader": {"entry_rva": "0x1b24", "table_pointer_literal": "0x6e1c8",
               "count_pointer_literal": "0x6e200", "record_address_formula": "base + 28*i",
               "stride": "0x1c", "record_member_loads": record_mem,
               "count_read": "u8[0x17100] = 2"},
    "table": {"conditional_base": "0x57100 (unproven)", "table_rva": hex(table_rva),
              "row0_plus4": hex(u32(table_rva + 4)), "row0_plus8": hex(u32(table_rva + 8)),
              "row1_plus8_offset": hex(row1_plus8), "row1_plus8": hex(u32(row1_plus8)),
              "candidate_0x5e479_consumed_by_this_reader": False},
    "checks_detail": checks,
}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
raise SystemExit(0 if result["status"] == "PASS" else 1)
