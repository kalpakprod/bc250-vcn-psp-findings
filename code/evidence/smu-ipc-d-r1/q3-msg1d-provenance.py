#!/usr/bin/env python3
"""Emit the bounded Q3 0x1D argument-flow conclusion for D-R1."""
from pathlib import Path
import hashlib

BODY = Path("/home/OWNER/orca/projects/bc250/import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body")

def main() -> None:
    b = BODY.read_bytes()
    print(f"body={BODY} size={len(b)} sha256={hashlib.sha256(b).hexdigest()}")
    print("q3_entry=msg_0x1d table_body_offset=0x754c handler=0x2e6c8 flags=0x00000006")
    print("arg_read=0x2e6cb mov a10,a2; 0x2e6cd call8 0xffc; 0x2e6d2 mov a3,a10")
    print("index_provenance=0x2e6d4 extui a10,a10,0x10,0x10 -> table index=arg[31:16]")
    print("value_provenance=0x2e6ef extui a14,a3,0x0,0x10 -> value=arg[15:0]")
    print("state_update=0x2e6ec addx2 then 0x2e6f8 addx4 -> table + 12*index; 0x2e6fb ssi f0,(table + 12*index),0x140; f0=ufloat(value)")
    print("post_update=0x2e6fe call8 0x2268; 0x2e701 call8 0x2e448 (no explicit packed-arg move at callsite)")
    print("call_2e448_args=0x2e448 local initialization dominates the first loop read; 0x2268 outgoing a10 is overwritten by 0x2e45b mov.n a2,a7")
    print("chain=0x2e6c8->0x2e701->0x2e448->0x2e481->0x23730->0x23735->0x246f4")
    print("downstream_2e448=coherent body reads f2=*(0x13ed4+12*i+0x14c), writes *(a2+0x5c), and loops a3=0x13ed4+4*i, a2=0x13ed4+12*i until a2==0x13fc4")
    print("downstream_246f4=0x2e481 receives d=a4 where a4=*(0x13ed4+4*i+8) from 0x2e46e; 0x23730 forwards d to 0x246f4")
    print("q3_field_alias=0x2e45b mov.n a2,a7 establishes a2=0x13ed4 before loop; 2e448 reads 0x14020+12*i, exactly Q3 msg1D writes for index=i+1 (indices 1..20) when 0x2e45d a8!=a9 enters loop")
    print("q3_domain_set_on_loop=0x0..0xd plus 0x13..0x18 (20 table iterations; float branches may reduce action)")
    print("q3_domain_source=2e448 a4_i=*(0x13ed4 + 4*i + 8), i=0..19; branch comparisons may reduce this candidate set")
    print("q3_domain_source_values=*(0x13ed4 + 4*i + 8), i=0..19 => [0xd,0x0,0x1,0x2,0x3,0x4,0x5,0x6,0x7,0xa,0x18,0x13,0x14,0x15,0x16,0x17,0xb,0x8,0x9,0xc]")
    print("helper_2268=0x2e6f2 loads literal *(0x17084)=0x40000; CALL8 maps it to 0x2268 incoming a2, and outgoing a10 is overwritten by 0x2e45b mov.n a2,a7 before first loop read")
    print("d_value_verdict=Q3 index/value are proven into indexed float storage and float fields are directly consumed on loop entry; d/value-to-domain action remains float-gated")
    print("hardware=unrun")

if __name__ == "__main__":
    main()
