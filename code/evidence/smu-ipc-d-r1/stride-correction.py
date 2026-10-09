#!/usr/bin/env python3
"""Reproduce D-R1 Xtensa stride, predicate, and Q3-chain corrections."""
from pathlib import Path
import hashlib
import struct

BODY = Path("/home/OWNER/orca/projects/bc250/import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body")

def u32(b: bytes, off: int) -> int:
    return struct.unpack_from("<I", b, off)[0]

def main() -> None:
    b = BODY.read_bytes()
    print(f"body_path={BODY}")
    print(f"body_size={len(b)} body_sha256={hashlib.sha256(b).hexdigest()}")
    print("pcode_stride_246f4=((d<<3)-d)<<2=28*d")
    print("pcode_stride_2362c=((d<<3)-d)<<2=28*d")
    record_base = u32(b, 0x178AC)
    slot_base = u32(b, 0x17434)
    lower, upper = u32(b, 0x17890), u32(b, 0x17894)
    print(f"table_bases=record:0x{record_base:x} slot:0x{slot_base:x}")
    print(f"forwarding=0x{lower + 1:x}..0x{upper:x} lower_exclusive=0x{lower:x}")
    for d in range(19, 25):
        record = record_base + 28 * d
        slot = b[record + 0x80]
        shift = b[record + 0x81]
        slot_record = slot_base + 72 * slot
        target = u32(b, slot_record + 0x44)
        print(f"246f4_row d={d} record=0x{record:x} slot={slot} shift={shift} slot_record=0x{slot_record:x} target=0x{target:08x} branch={'ipc' if slot == 0 else 'local'} in_forward={lower < target <= upper}")
    for d in range(14, 19):
        field = slot_base + 28 * d + 0x254
        target = u32(b, field)
        print(f"2362c_target d={d} field=0x{field:x} target=0x{target:08x} in_forward={lower < target <= upper}")
    print("q3_basis=body_offset_0x746c; inner_dump_coordinate=0x8ff200+0x736c; same_spi=0x90656c")
    print("q3_chain=msg_0x1d@0x754c->handler_0x2e6c8->call_0x2e701->0x2e448->call_0x2e481->0x23730->call_0x23735->0x246f4")
    print("scanner=every-byte direct-instruction candidates; scope=0x0..0x3a000; omitted=0x3a000..0x40000; indirect_edges=unresolved")

if __name__ == "__main__":
    main()
