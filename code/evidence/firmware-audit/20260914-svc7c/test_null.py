"""Bounded exact-code execution; no hardware model or hardware access."""
from pathlib import Path
import hashlib
import json
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

root = Path(__file__).resolve().parents[3]
rom = (root/'evidence/programmer/reads/20260914-identification/read-a.bin').read_bytes()
body = rom[0x8ead00:0x8fef50]
assert hashlib.sha256(body).hexdigest() == '3b52b28e6f4642e7c8f09f2ddf14d957968d32f651e84bf81acf8b38f5ca43e9'
results = []
for target in (0x0900c004, 0x03700000, 0x03900000, 0xfffffffc):
    for width in (1, 2, 4, 3):
        mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        mu.mem_map(0, 0x20000)
        mu.mem_write(0, body)
        mu.mem_map(0x1000000, 0x100000)
        mu.mem_map(0x2000000, 0x10000)
        mu.reg_write(UC_ARM_REG_SP, 0x200f000)
        mu.reg_write(UC_ARM_REG_LR, 0x1f001)
        for reg,value in [(UC_ARM_REG_R0,target),(UC_ARM_REG_R1,0xa5a5a5a5),(UC_ARM_REG_R2,width),(UC_ARM_REG_R3,0)]:
            mu.reg_write(reg,value)
        writes = []
        hooks = []
        def code(uc,addr,size,user):
            if addr == 0x42d8:
                hooks.append('hardware_selector_skipped')
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        def write(uc,access,addr,size,value,user):
            if addr < 4 or 0x1000000 <= addr < 0x1100000:
                writes.append(dict(address=hex(addr),size=size,value=hex(value)))
        mu.hook_add(UC_HOOK_CODE,code)
        mu.hook_add(UC_HOOK_MEM_WRITE,write)
        mu.emu_start(0x5a89, 0x1f000, count=200)
        assert mu.reg_read(UC_ARM_REG_PC) == 0x1f000
        result = mu.reg_read(UC_ARM_REG_R0)
        if width == 3:
            assert not writes and result == 5
        else:
            assert len(writes) == 1 and result == 0
            expected = 0x100c004 if target == 0x0900c004 else 0
            assert int(writes[0]['address'],16) == expected
        results.append(dict(target=hex(target),width=width,status=result,writes=writes,hooks=hooks))
print(json.dumps(dict(classification='emulated-exact-code',cases=results,
    limitations=['Synthetic writable address0', 'Hardware selector stubbed for accepted control',
                 'Caller authorization and live VBAR not tested', 'No VCN unlock proof']),indent=2))
