"""Extract the audited table layout from one hash-pinned PMFW body, offline."""
import hashlib
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[3]
source = root / 'import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body'
data = source.read_bytes()
digest = hashlib.sha256(data).hexdigest()
assert digest == '5c805026581ace101ba43ef4d0f6b34354f4a61461a1c78d2fa6a335a53d9936'
def u32(offset):
    return struct.unpack_from('<I', data, offset)[0]
domain_base = u32(0x17434)
slot_base = u32(0x178ac) + 0x80
assert (domain_base, slot_base) == (0xf550, 0xf790)
slots = []
for index in range(27):
    offset = slot_base + 28 * index
    domain = data[offset]
    assert domain < 8
    slots.append(dict(index=index, offset=hex(offset), domain_index=domain,
                      domain_local_slot=data[offset+1],
                      programming_address=hex(u32(domain_base+0x254+28*index)),
                      semantic_name=None))
domains = []
for index in range(8):
    offset = domain_base + 72 * index
    base = u32(offset + 8)
    domains.append(dict(index=index, offset=hex(offset), block_base=hex(base),
        image_state_byte=data[offset+0x14],
        native_local_addresses={name:hex(0x1100000+((base+u32(offset+field))&0xfffff))
            for name,field in [('status',0x34),('control',0x38),('sequencer',0x3c)]}))
readback = root / 'evidence/programmer/reads/20260912/d19/postwrite-d19.bin'
assert readback.read_bytes()[0x8ff100:0x93f100] == data
print(json.dumps(dict(classification='static-analysis', source=str(source.relative_to(root)),
    sha256=digest, body_matches_d19=True, slots=slots, domains=domains,
    limitations=['No current hardware state', 'No clock names proven',
                 'Native local addresses are not proven host SMN aliases']), indent=2))
