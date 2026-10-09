#!/usr/bin/env python3
"""Machine-generated CALL8/ENTRY and ordered 0x2E448 def-use table."""
from __future__ import annotations

import re
import struct
from pathlib import Path

import pypcode

BODY = Path("/home/OWNER/orca/projects/bc250/import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body")
TRACK = ("a2", "a3", "a5", "a7")
FALLBACK_LENGTHS = {0x2E451: 3}


def decode(ctx: pypcode.Context, data: bytes, address: int):
    try:
        return ctx.disassemble(data, base_address=address, offset=address, max_instructions=1).instructions[0]
    except pypcode.BadDataError as exc:
        return exc


def main() -> None:
    data = BODY.read_bytes()
    ctx = pypcode.Context("Xtensa:LE:32:default")
    print(f"body={BODY} size={len(data)}")
    print("call8_abi=caller outgoing a10/a11 -> callee incoming a2/a3 after window rotation")
    print("function=0x2e448 coherent range 0x2e448..0x2e501; instruction boundaries are reconstructed sequentially")
    for address in (0x2E6FE, 0x2E701, 0x2E47F, 0x2E481):
        ins = decode(ctx, data, address)
        if isinstance(ins, Exception):
            print(f"call_context address=0x{address:05x} undecodable={ins}")
            continue
        ops = [str(op) for op in ctx.translate(data, base_address=address, offset=address, max_instructions=1).ops if op.opcode.name != "IMARK"]
        print(f"call_context address=0x{address:05x} mnemonic={ins.mnem} body='{ins.body.strip()}' pcode={' ; '.join(ops)}")
    print("address\tmnemonic\tbody\tdefs\tuses\tpcode")
    address = 0x2E448
    while address <= 0x2E4FF:
        ins = decode(ctx, data, address)
        if isinstance(ins, Exception):
            fallback = FALLBACK_LENGTHS.get(address)
            print(f"0x{address:05x}\tUNDECODABLE\t{ins}\t-\t-\tfallback_length={fallback or 'none'} raw={data[address:address + (fallback or 3)].hex()} note=GNU Xtensa cross-decoder identifies non-branch const.s f1,0")
            if fallback is None:
                break
            address += fallback
            continue
        body = ins.body.strip()
        ops = [str(op) for op in ctx.translate(data, base_address=address, offset=address, max_instructions=1).ops if op.opcode.name != "IMARK"]
        defs = []
        uses = []
        for op in ops:
            lhs = re.match(r"^(a[2357]) =", op)
            if lhs and lhs.group(1) not in defs:
                defs.append(lhs.group(1))
            rhs = op.split(" = ", 1)[1] if " = " in op else op
            for reg in TRACK:
                if re.search(rf"\b{reg}\b", rhs) and reg not in uses:
                    uses.append(reg)
        print(f"0x{address:05x}\t{ins.mnem}\t{body}\t{','.join(defs) or '-'}\t{','.join(uses) or '-'}\t{' ; '.join(ops) or '-'}")
        address += ins.length
    for address in (0x2E44B, 0x2E44E):
        ins = decode(ctx, data, address)
        literal = int(ins.body.split("0x", 1)[1].split()[0], 16) & 0x3FFFF
        print(f"literal address=0x{address:05x} target=0x{literal:05x} value=0x{struct.unpack_from('<I', data, literal)[0]:08x}")
    a7 = struct.unpack_from("<I", data, 0x181E0)[0]
    a5 = struct.unpack_from("<I", data, 0x181E4)[0]
    domains = [struct.unpack_from("<I", data, a7 + 4 * i + 8)[0] for i in range(20)]
    print(f"entry_definitions=a7=0x{a7:05x} @0x2e44b; a5=0x{a5:05x} @0x2e44e; a2=a7=0x{a7:05x} @0x2e45b; a3=a7 @0x2e466")
    print("loop_backedge=0x2e4f3 a3+=4; 0x2e4f5 a2+=12; 0x2e4f7 compares a2 to a5; 0x2e4fa branches to 0x2e468")
    print("q3_index_range=1..20; q3_value_field=*(0x13ed4 + 12*index + 0x140)")
    print("domain_values_on_loop_entry=" + ",".join(f"0x{x:x}" for x in domains))
    print("domain_set_on_loop_entry=" + ",".join(f"0x{x:x}" for x in sorted(set(domains))))
    print("consumer_float=0x2e468 reads *(0x13ed4 + 12*i + 0x14c) on loop entry path; this equals q3 field *(0x13ed4 + 12*(i+1) + 0x140) for index=i+1")
    print("consumer_domain=0x2e46e reads *(0x13ed4 + 4*i + 8); 0x2e47f->0x23730->0x246f4 receives that value as d")
    print("a2_producer=0x2e45b mov.n a2,a7; 0x2e451 EXCW/const.s f1,0 is non-branch under GNU floating-point configurations; 0x2e45d enters loop only when a8!=a9")
    print("helper_2268_return=outgoing a10 at 0x2e701; overwritten by local a2=a7 before first loop read")
    print("verdict=Q3-updated float field read is direct after local a2=a7 on the a8!=a9 loop path; d/value direct propagation to 0x246f4 remains float-gated and unproven")


if __name__ == "__main__":
    main()
