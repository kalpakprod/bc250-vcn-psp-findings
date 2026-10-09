# Find all uses of the located APCB interface global (@+0x6750) in AmdFabricAriDxe
# and the vtable offsets called through it.
import struct, re
import capstone

DIR = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"
fn = DIR + r"\FV@ae0000_0b_9E21FD93_78.LZMA.dec_07_25075106_6b28c.PE32"
d = open(fn, "rb").read()

e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
nsec = struct.unpack_from("<H", d, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", d, e_lfanew + 20)[0]
secoff = e_lfanew + 24 + optsz
imagebase = struct.unpack_from("<Q", d, e_lfanew + 24 + 24)[0]
secs = []
for i in range(nsec):
    o = secoff + 40 * i
    nm = d[o:o + 8].rstrip(b"\x00").decode()
    vsz, vaddr, rsz, raddr = struct.unpack_from("<IIII", d, o + 8)
    secs.append((nm, vaddr, vsz, raddr, rsz))

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

tstart, tlen = secs[0][3], secs[0][4]
insn_by_addr = {}
for ins in md.disasm(d[tstart:tstart + tlen], imagebase + secs[0][1]):
    insn_by_addr[ins.address] = ins

# find every rip-ref that targets RVA 0x6750 (the APCB iface global)
GL = imagebase + 0x6750
refs = []
for ins in insn_by_addr.values():
    if "rip" in ins.op_str and ins.mnemonic in ("mov", "lea"):
        mm = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", ins.op_str)
        if mm:
            tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
            if tgt == GL:
                refs.append(ins)

print("refs to APCB-iface global @0x6750:", len(refs))
for ins in refs:
    print("  %#x: %s %s" % (ins.address, ins.mnemonic, ins.op_str))

# for each 'mov rXX, [global]' find subsequent 'call [rXX + off]' within 12 insns
print("\n=== vtable call patterns ===")
for ins in refs:
    if ins.mnemonic != "mov" or not ins.op_str.startswith("r"):
        continue
    m = re.match(r"(\w+), qword ptr \[rip", ins.op_str)
    if not m:
        continue
    reg = m.group(1)
    a = ins.address
    cnt = 0
    for _ in range(14):
        nxt = None
        for delta in range(1, 16):
            if a + delta in insn_by_addr:
                nxt = insn_by_addr[a + delta]
                break
        if nxt is None:
            break
        a = nxt.address
        if nxt.mnemonic == "call" and nxt.op_str.startswith("qword ptr [%s" % reg):
            print("  from %#x: call %s  (delta %d insns)" % (ins.address, nxt.op_str, cnt))
            break
        cnt += 1
