# Disasm AmiApcbLibInterface entry: find Install/LocateProtocol GUIDs; dump .data GUID-ish blobs.
import struct, sys
import capstone

DIR = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"
fn = DIR + r"\FV@ae0000_0b_9E21FD93_78.LZMA.dec_07_C92C9385_b5270.PE32"
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


def off_of_file(x):
    return x


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# entry point
ep = struct.unpack_from("<I", d, e_lfanew + 24 + 16)[0]
print("entry RVA:", hex(ep))
# find file offset of entry
def rva2off(rva):
    for nm, vaddr, vsz, raddr, rsz in secs:
        if vaddr <= rva < vaddr + max(vsz, rsz):
            return raddr + (rva - vaddr)
    return None


eo = rva2off(ep)
print("entry file off:", hex(eo))

# collect all gBS->foo calls with lea rcx,[rip+..] just before: scan whole .text for pattern
# call qword ptr [rax + 0x140/0x128] preceded by lea rcx,[rip+X]
text = secs[0]
tstart = text[3]
tend = tstart + text[4]
calls = []
i = tstart
code = d[tstart:tend]
for ins in md.disasm(code, imagebase + text[1]):
    if ins.mnemonic == "call" and ins.op_str.startswith("qword ptr ["):
        calls.append(ins)

print("\ngBS-style indirect calls (offsets 0x128 LocateProtocol / 0x140 InstallProtocolInterface):")
import re
for ins in md.disasm(code, imagebase + text[1]):
    m = re.match(r"qword ptr \[(\w+) \+ (0x[0-9a-f]+)\]", ins.op_str)
    if ins.mnemonic == "call" and m and m.group(2) in ("0x128", "0x140", "0x130", "0x138"):
        print("  %#x call [r%s+%s]" % (ins.address, m.group(1), m.group(2)))

# Simpler: disasm entry region and print
print("\n=== entry disasm ===")
for ins in md.disasm(d[eo:eo + 0x300], imagebase + ep):
    ann = ""
    if "rip" in ins.op_str:
        mm = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", ins.op_str)
        if mm:
            tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
            for nm, vaddr, vsz, raddr, rsz in secs:
                if vaddr <= tgt - imagebase < vaddr + max(vsz, rsz):
                    o = raddr + (tgt - imagebase - vaddr)
                    s = d[o:o + 64].split(b"\x00")[0]
                    if s and all(32 <= c < 127 for c in s[:min(len(s), 32)]):
                        ann = '  ; "%s"' % s.decode()
                    else:
                        ann = "  ; @+%#x: %s" % (o, d[o:o + 16].hex(" "))
                    break
    print("%#08x  %-22s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, ann))

# dump all 16B-aligned blobs in third section (0x22c0) and .data start
print("\n=== data section blob dump (0x19a0..0x22c0) ===")
for o in range(0x19a0, min(0x22c0, len(d)), 8):
    b = d[o:o + 16]
    if b.count(0) < 12 and b != b"\xff" * 16:
        print("+%#x: %s" % (o, b.hex(" ")))
