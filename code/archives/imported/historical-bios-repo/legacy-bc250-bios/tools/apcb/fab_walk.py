# Disasm AmdFabricAriDxe 0x460..0xb40 - the region with FabricRegisterAcc call clusters
# (likely the DFG record apply loop), with rip-annotations.
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
secs = []
for i in range(nsec):
    o = secoff + 40 * i
    nm = d[o:o + 8].rstrip(b"\x00").decode()
    vsz, vaddr, rsz, raddr = struct.unpack_from("<IIII", d, o + 8)
    secs.append((nm, vaddr, vsz, raddr, rsz))


def rva2off(rva):
    for nm, vaddr, vsz, raddr, rsz in secs:
        if vaddr <= rva < vaddr + max(vsz, rsz):
            return raddr + (rva - vaddr)
    return None


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

a, b = int(sys.argv[1], 16), int(sys.argv[2], 16)
for ins in md.disasm(d[a:b], imagebase + a):
    ann = ""
    if "rip" in ins.op_str:
        mm = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", ins.op_str)
        if mm:
            tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
            o2 = rva2off(tgt - imagebase)
            if o2 is not None:
                s = d[o2:o2 + 64].split(b"\x00")[0]
                if s and all(32 <= c < 127 for c in s[:min(len(s), 40)]):
                    ann = '  ; "%s"' % s.decode()
                else:
                    ann = "  ; @+%#x %s" % (o2, d[o2:o2 + 16].hex(" "))
    mark = " <<<<" if (ins.mnemonic == "call" and "0x307c" in ins.op_str) else ""
    print("%#08x  %-24s %s %s%s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, ann, mark))
