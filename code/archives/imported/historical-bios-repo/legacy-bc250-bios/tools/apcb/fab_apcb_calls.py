# In AmdFabricAriDxe: find LocateProtocol(APCB GUID) usage, dump entry, find vtable calls
# on the APCB interface, and dump the record-walk that feeds 0x2924/0x307c.
import struct, sys, re
import capstone

DIR = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"
fn = DIR + r"\FV@ae0000_0b_9E21FD93_78.LZMA.dec_07_25075106_6b28c.PE32"
d = open(fn, "rb").read()

e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
nsec = struct.unpack_from("<H", d, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", d, e_lfanew + 20)[0]
secoff = e_lfanew + 24 + optsz
imagebase = struct.unpack_from("<Q", d, e_lfanew + 24 + 24)[0]
ep_rva = struct.unpack_from("<I", d, e_lfanew + 24 + 16)[0]
secs = []
for i in range(nsec):
    o = secoff + 40 * i
    nm = d[o:o + 8].rstrip(b"\x00").decode()
    vsz, vaddr, rsz, raddr = struct.unpack_from("<IIII", d, o + 8)
    secs.append((nm, vaddr, vsz, raddr, rsz))
    print("sec %-8s VA=%#x VSZ=%#x RAW=%#x RSZ=%#x" % (nm, vaddr, vsz, raddr, rsz))


def rva2off(rva):
    for nm, vaddr, vsz, raddr, rsz in secs:
        if vaddr <= rva < vaddr + max(vsz, rsz):
            return raddr + (rva - vaddr)
    return None


def off2rva(off):
    for nm, vaddr, vsz, raddr, rsz in secs:
        if raddr <= off < raddr + rsz:
            return vaddr + (off - raddr)
    return None


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# where is the APCB GUID in this module?
APCB_G = bytes.fromhex("f6ca57e846c0dc45be3fee0765fba887")
gi = d.find(APCB_G)
print("\nAPCB GUID @+%#x (RVA %#x)" % (gi, off2rva(gi) or 0))

# scan .text for lea/mov referencing gi's RVA
lea_refs = []
tstart, tlen = secs[0][3], secs[0][4]
for ins in md.disasm(d[tstart:tstart + tlen], imagebase + secs[0][1]):
    if ins.mnemonic in ("lea", "mov", "push") and "rip" in ins.op_str:
        mm = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", ins.op_str)
        if mm:
            tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
            if off2rva(gi) is not None and tgt == imagebase + off2rva(gi):
                lea_refs.append(ins.address)
print("refs to APCB GUID:", ["%#x" % a for a in lea_refs])

# disasm around each ref
for a in lea_refs:
    o = rva2off(a - imagebase)
    print("\n===== around GUID ref %#x (+%#x) =====" % (a, o))
    for ins in md.disasm(d[o - 0x40:o + 0x100], imagebase + off2rva(o - 0x40)):
        print("%#08x  %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

# entry disasm
eo = rva2off(ep_rva)
print("\n===== entry (RVA %#x, file +%#x) =====" % (ep_rva, eo))
for ins in md.disasm(d[eo:eo + 0x200], imagebase + ep_rva):
    ann = ""
    if "rip" in ins.op_str:
        mm = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", ins.op_str)
        if mm:
            tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
            o2 = rva2off(tgt - imagebase)
            if o2 is not None:
                s = d[o2:o2 + 64].split(b"\x00")[0]
                if s and all(32 <= c < 127 for c in s[:min(len(s), 32)]):
                    ann = '  ; "%s"' % s.decode()
                else:
                    ann = "  ; @+%#x %s" % (o2, d[o2:o2 + 16].hex(" "))
    print("%#08x  %-22s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, ann))
