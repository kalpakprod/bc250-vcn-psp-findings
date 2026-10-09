# Disassemble x86-64 regions around SMN/NBIO constants in AmdFabricAriDxe / AmdNbioIOMMUARIDxe.
import struct, sys
import capstone

fn = sys.argv[1]
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
    print("sec %-8s VA=%#x VSZ=%#x RAW=%#x RSZ=%#x" % (nm, vaddr, vsz, raddr, rsz))


def va_of_off(off):
    for nm, vaddr, vsz, raddr, rsz in secs:
        if raddr <= off < raddr + rsz:
            return imagebase + vaddr + (off - raddr)
    return None


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

TARGETS = [0x1c7e980, 0x1c74910, 0x1c74902, 0x1c7f641, 0x1c7e980]


def dis(a, b, note):
    print("\n===== +%#x..+%#x  %s =====" % (a, b, note))
    for ins in md.disasm(d[a:b], va_of_off(a) or a):
        ann = ""
        if "rip" in ins.op_str:
            import re as _re
            mm = _re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", ins.op_str)
            if mm and ins.mnemonic in ("lea", "mov"):
                tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
                # find file offset
                for nm, vaddr, vsz, raddr, rsz in secs:
                    if vaddr <= tgt - imagebase < vaddr + max(vsz, rsz):
                        o = raddr + (tgt - imagebase - vaddr)
                        s = d[o:o + 56].split(b"\x00")[0]
                        if s and all(32 <= c < 127 for c in s[:min(len(s), 28)]):
                            ann = '  ; "%s"' % s.decode()
                        else:
                            ann = "  ; data@+%#x" % o
                        break
        print("%#08x  %-22s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, ann))


for t in set(TARGETS):
    pat = struct.pack("<I", t)
    i = -1
    while True:
        i = d.find(pat, i + 1)
        if i < 0:
            break
        a = (i - 0x60) & ~0xF
        dis(a, i + 0x60, "const %#x @+%#x" % (t, i))
