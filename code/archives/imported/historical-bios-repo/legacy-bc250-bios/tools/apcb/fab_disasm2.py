# Disassemble specific functions in AmdFabricAriDxe: record-type switch, case6, writer 0x307c, and callers.
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


def va_of_off(off):
    for nm, vaddr, vsz, raddr, rsz in secs:
        if raddr <= off < raddr + rsz:
            return imagebase + vaddr + (off - raddr)
    return None


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)


def dis(a, b, note):
    print("\n===== +%#x..+%#x  %s =====" % (a, b, note))
    for ins in md.disasm(d[a:b], va_of_off(a) or a):
        ann = ""
        if "rip" in ins.op_str:
            import re as _re
            mm = _re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", ins.op_str)
            if mm and ins.mnemonic in ("lea", "mov"):
                tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
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


REGIONS = [
    (0x2924, 0x2a80, "DFG record-type switch (full)"),
    (0x2a80, 0x2c00, "after switch / caller area"),
    (0x307c, 0x3260, "function 0x307c (record writer?)"),
    (0x3e80, 0x3fc0, "loop calling 0x307c with 0x3fc"),
    (0x858, 0xa80, "entry func with 0x114/0x28 + 0x307c calls"),
]
for a, b, note in REGIONS:
    dis(a, b, note)

# find all call sites to 0x2924 and 0x307c
print("\n=== call sites ===")
for tgt in (0x2924, 0x307c):
    for i in range(0, len(d) - 5):
        if d[i] == 0xE8:
            rel = struct.unpack_from("<i", d, i + 1)[0]
            dest = i + 5 + rel
            if dest == tgt:
                print("call %#x from +%#x" % (tgt, i))
