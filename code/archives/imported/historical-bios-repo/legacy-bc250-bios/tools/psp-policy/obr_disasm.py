# x86-64 disassembly hunter for AmdApcbObr(Dxe|Smm): gid switch + DFG token processing.
import sys
import capstone

fn = sys.argv[1]
d = open(fn, "rb").read()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = False

# PE image: map sections (assume flat; find .text via PE header)
import struct
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


def off_of_va(va):
    for nm, vaddr, vsz, raddr, rsz in secs:
        if vaddr <= va < vaddr + max(vsz, rsz):
            return raddr + (va - vaddr)
    return None


def va_of_off(off):
    for nm, vaddr, vsz, raddr, rsz in secs:
        if raddr <= off < raddr + rsz:
            return imagebase + vaddr + (off - raddr)
    return None


def disasm_region(a, b, note=""):
    print("\n===== %#x .. %#x %s =====" % (a, b, note))
    code = d[a:b]
    for ins in md.disasm(code, va_of_off(a) or a):
        extra = ""
        # annotate lea rip-relative string refs
        m = ins.op_str
        if "rip" in m and ("lea" in ins.mnemonic or "mov" in ins.mnemonic):
            try:
                import re as _re
                mm = _re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", m)
                if mm:
                    tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
                    o = off_of_va(tgt)
                    if o is not None:
                        s = d[o:o + 48]
                        txt = s.split(b"\x00")[0]
                        if txt and all(32 <= c < 127 for c in txt[:min(len(txt), 24)]):
                            extra = "  ; \"%s\"" % txt.decode()
                        else:
                            extra = "  ; data@%#x" % o
            except Exception:
                pass
        if ins.mnemonic in ("call", "jmp") and "0x" in ins.op_str:
            pass
        print("%#08x  %-24s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, extra))


# 1) gid immediate sites
for gid, nm in ((0x1701, "PSPG"), (0x1702, "CCXG"), (0x1703, "DFG"), (0x1704, "MEMG"), (0x1705, "GNBG"), (0x17FF, "INVAL")):
    pat = struct.pack("<I", gid)
    i = -1
    while True:
        i = d.find(pat, i + 1)
        if i < 0:
            break
        # keep only imm32-like contexts (b8/bd/be/bf mov imm, or 3d/81 cmp)
        ctx = d[max(0, i - 2):i]
        if any(c in ctx[-1:] for c in b"\x81\x3d\xb8\xbd\xbe\xbf\xbf") or True:
            print("gid %s @file+%#x ctx=%s" % (nm, i, d[max(0, i - 6):i + 8].hex(" ")))

# 2) disassemble around the main cluster (first DFG site -0x180..+0x280)
i = d.find(struct.pack("<I", 0x1703))
if i >= 0:
    a = (i - 0x180) & ~0xF
    disasm_region(a, i + 0x300, "gid cluster")
