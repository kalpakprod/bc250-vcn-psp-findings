#!/usr/bin/env python3
"""Direct, non-mutating read of one Queue 3 selector through the exact payload tables."""
from pathlib import Path
import hashlib, struct
rom_path=Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
smu_path=Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
rom=rom_path.read_bytes(); b=smu_path.read_bytes()
u8=lambda o:b[o]
u32=lambda o:struct.unpack_from('<I',b,o)[0]
f32=lambda o:struct.unpack_from('<f',b,o)[0]
print('rom_sha256='+hashlib.sha256(rom).hexdigest()+f' rom_size={len(rom)}')
print('smu_sha256='+hashlib.sha256(b).hexdigest()+f' smu_size={len(b)} embedded_equal={rom[0x8FEF00:0x8FEF00+len(b)]==b}')
print(f'preserve1800: ROM[0x7E5]=0x{rom[0x7E5]:02X} (AmdSetup+0x316)')
selector=11; loop_i=selector-1
write_slot=0x13EEC+0x140+selector*12
read_slot=0x13EEC+0x14C+loop_i*12
domain_cell=0x13EEC+0x08+loop_i*4
domain=u32(domain_cell)
group_desc=0xF7A8+domain*0x1C
group=u8(group_desc)
program_cell=0xF7BC+domain*0x1C
program_offset=u32(program_cell)
mask=u32(0x17134); smu_window=u32(0x17160)+0x200
program=smu_window+(program_offset&mask)
poll=smu_window+((program_offset+0x24)&mask)
print(f'selector={selector} loop_i={loop_i} write_slot=0x{write_slot:05X} read_slot=0x{read_slot:05X} domain_cell=0x{domain_cell:05X} domain_id=0x{domain:02X}')
print(f'domain_descriptor=0x{group_desc:05X} group_id={group} program_pointer_cell=0x{program_cell:05X} raw_program_offset=0x{program_offset:05X}')
print(f'SMU_window_base=0x{smu_window:08X} program=0x{program:08X} poll=0x{poll:08X} IPC_interval=0x{u32(0x178B8):05X}..0x{u32(0x178BC):05X}')
for n in (12,13,14):
 i=n-1; did=u32(0x13EEC+0x08+i*4); g=u8(0xF7A8+did*0x1C); reg=u32(0xF7BC+did*0x1C)
 print(f'neighbor_selector={n} domain_id=0x{did:02X} group_id={g} raw_program_offset=0x{reg:05X} handler_filter={"denied" if did in (0x13,0x14) else "not-denied"}')
scale_ptr=u32(0x18240)
print(f'low16_scale_pointer=0x{scale_ptr:05X} scale_float={f32(scale_ptr):.9f}')
print(f'group_vco_factors: 0x17924={f32(0x17924):.9f}, 0x17928={f32(0x17928):.1f}; U9.16 fraction literal=0x17460 {f32(0x17460):.12f}')
print(f'static_group6_base_word_at_0x{0xF568+6*0x48:05X}=0x{u32(0xF568+6*0x48):08X} (runtime population unresolved)')
print('source-unit-label=not encoded/proven; no MHz assignment')
