#!/usr/bin/env python3
"""Bounded source/consumer trace for exact CLV SMU clock request candidates."""
from pathlib import Path
import hashlib, json, struct

ROM = Path("evidence/donor/retroweb-20260916/BC250_5.00_clv.bin")
SMU = Path("import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5")
rom = ROM.read_bytes(); b = SMU.read_bytes()
assert len(rom) == 0x1000000
assert hashlib.sha256(rom).hexdigest() == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
assert len(b) == 262400
assert hashlib.sha256(b).hexdigest() == "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37"
assert rom[0x8FEF00:0x8FEF00+len(b)] == b
assert rom[0x7E5] == 0x24

def u8(o): return b[o]
def u16(o): return struct.unpack_from('<H', b, o)[0]
def u32(o): return struct.unpack_from('<I', b, o)[0]
def f32(o): return struct.unpack_from('<f', b, o)[0]
def chk(cond, msg):
    assert cond, msg
    checks.append(msg)
checks=[]
# Shared state pointers and preserved CLV request.
chk(u32(0x1711C) == 0x7B5C, "PPTable committed base literal 0x1711C=0x7B5C")
chk(u32(0x17118) == 0x7FF8, "PPTable staging base literal 0x17118=0x7FF8")
chk(rom[0x7E5] == 0x24, "CLV AmdSetup+0x316 byte 0x24 (1800-labelled request) preserved")
# Dynamic Queue 3 0x1D: mailbox -> target float -> actuator.
chk(u32(0x7554) == 0x2EA08, "Queue 3 0x1D handler pointer 0x2EA08")
chk(b[0x2EA14:0x2EA1A] == bytes.fromhex('a0a0f5a73c3f'), "0x2EA08 extracts high16 index and bounds-checks")
chk(b[0x2EA2F:0x2EA3E] == bytes.fromhex('30e0f4a198a1000edad0cca0034c50'), "0x2EA08 converts low16 request and stores target float")
chk(b[0x2EA41:0x2EA44] == bytes.fromhex('65d4ff'), "0x2EA08 calls actuator loop 0x2E788")
chk(b[0x2E9E1:0x2EA03] == bytes.fromhex('51cea18114a642a06440428229185024804115a676a30a8222120008da4b2203c403'), "0x2E9DC loads bulk targets from 0x7B5C+pstate*100+0x48")
chk(b[0x2E788:0x2E791] == bytes.fromhex('36410071aaa651aaa6'), "0x2E788 uses state base 0x13EEC")
chk(b[0x23890:0x238B2] == bytes.fromhex('366100411ad02052f0e055114a45a2048061eecea08ab06088b08208146a55522595'), "0x23890 reaches domain descriptor and program path")
chk(b[0x235C8:0x23607] == bytes.fromhex('3641000c4aa5a406b1d9ce8d0aa1e2ce8cb8b09210aa99c020003269801df0c1b4d0b0e210aaee27bc0ed1b2d0273d08ad02bd0365f1f71df0c02000326e80'), "0x235C8 entry is present")
# Queue 4 raw ID 0x07: selector -> static table -> actuators.
chk(u32(0x79EC) == 0x1E720, "raw Queue ID 4 msg 0x07 handler pointer 0x1E720")
chk(b[0x1E72D:0x1E739] == bytes.fromhex('876a129204f7a08074973809'), "0x1E720 validates mode bit and pstate bound")
chk(b[0x1E74C:0x1E75E] == bytes.fromhex('30a874b2a0ffb244f6661a1bd204f7324416'), "0x1E720 takes high-byte mode and low-byte pstate")
chk(b[0x1E78C:0x1E78F] == bytes.fromhex('a5cbff'), "0x1E720 calls DF applier 0x1E448")
chk(b[0x1E448:0x1E46E] == bytes.fromhex('3661003168e38203f787320246490022430e3062a09876a2a400520900420901720903030901'), "0x1E448 loads row pointer and row[0..3]/row+4")
chk(b[0x1E4BD:0x1E4CE] == bytes.fromhex('e876a20e08b20e09c20e0ad20e0be20e0c'), "0x1E448 reads row offsets 8..12 for actuator arguments")
chk(b[0x1E53A:0x1E562] == bytes.fromhex('256405c2030d30cca0c87ca20c0ab20c08c20c09a56505c2030d30cca0c87ca20c0cb20c08c20c0b'), "0x1E448 calls DF actuator helpers")
# Static table and exact P3 row; no AmdSetup source join.
table = 0xCF0C + 3*0x28
chk(table == 0xCF84, "P-state 3 row address 0xCF84")
chk(bytes(b[table:table+4]) == bytes.fromhex('270d0000'), "P-state 3 DF row bytes 0x27,0x0D")
chk(abs(f32(table+4)-1200.0) < 1e-6 and abs(f32(table+16)-875.0) < 1e-6 and abs(f32(table+20)-109.375) < 1e-6, "P-state 3 stored rate floats are 1200/875/109.375")
chk(abs(f32(table+24)-1750.0) < 1e-6, "P-state 3 row+0x18 stores 1750.0 but is not joined to this actuator")
# Unit/selector discrimination.
def dfs(code):
    if code <= 0x40: return code*0.25
    if code <= 0x60: return (code*2-0x40)*0.25
    if code <= 0x7e: return (code*4-0x100)*0.25
    return 128.0
def rate(raw,did):
    return ((raw & 0x1ff) + ((raw>>16)&0xffff)/65536.0) * 0.1 / dfs(did) * 1000.0
chk(abs(rate(u8(table),u8(table+1))-1200.0)<1e-6, "P-state 3 domain 0x0E fixed-point/DID arithmetic reconstructs 1200")
chk(abs(rate(u8(table+8),u8(table+9))-875.0)<1e-6, "P-state 3 domain 0x0F/0x11 arithmetic reconstructs 875")
chk(abs(rate(u8(table+8),u8(table+11))-109.375)<1e-6, "P-state 3 domain 0x10/0x12 arithmetic reconstructs 109.375")
result={
  "status":"PASS", "checks":len(checks),
  "source_edges": {
    "q3_0x1d": {"mailbox":"Queue ID 3 msg 0x1D", "handler":"0x2EA08", "target_source":"low16 mailbox arg -> ufloat.s -> 0x1402C+index*12", "bulk_source":"0x2E9DC reads 0x7B5C+pstate*100+0x48 -> 0x14038", "consumer":"0x2E788 -> 0x23890 -> 0x235C8", "unit":"raw unsigned integer; no MHz/divider scale encoded", "setup_join":"not observed"},
    "q4_0x07": {"mailbox":"raw Queue ID 4 msg 0x07", "dispatch":"0x79E8/0x79EC", "handler":"0x1E720 -> 0x1E448", "selector":"high byte mode 0x01, low byte pstate index", "table":"0xCF0C, 5 rows x 0x28", "consumer":"0x23B7C/0x23BA8/0x23BF4 -> 0x23F18", "unit":"fixed-point/DID arithmetic reproduces numeric stored floats; physical MHz identity unresolved", "setup_join":"not observed"}
  },
  "pstate3": {"row":"0xCF84", "stored_plus_0x04":1200.0, "stored_plus_0x10":875.0, "stored_plus_0x14":109.375, "stored_plus_0x18":1750.0},
  "preserved_clv_request":{"rom_offset":"0x7E5","AmdSetup_offset":"0x316","byte":"0x24","label":"1800MHz"},
  "unresolved":"provider/caller join from native AmdSetup/ABL1/APOB to mailbox args; physical MCLK/UCLK/FCLK assignment and crossing selector"
}
Path("evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/source-consumer-result.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, sort_keys=True))
