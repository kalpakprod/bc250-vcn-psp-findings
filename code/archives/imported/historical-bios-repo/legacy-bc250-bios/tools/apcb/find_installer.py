# Who INSTALLS E857CAF6 (APCB/PSP protocol)? Scan all PE32 modules for
# call [reg+0x80] (InstallProtocolInterface) with rcx/rdx lea -> the GUID.
# Also dump the vtable shape by looking at the installer's InstallProtocolInterface args.
import glob, struct, re
import capstone

DIR = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"
APCB_G = bytes.fromhex("f6ca57e846c0dc45be3fee0765fba887")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)


def secs_of(d):
    e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, e_lfanew + 6)[0]
    optsz = struct.unpack_from("<H", d, e_lfanew + 20)[0]
    secoff = e_lfanew + 24 + optsz
    imagebase = struct.unpack_from("<Q", d, e_lfanew + 24 + 24)[0]
    out = []
    for i in range(nsec):
        o = secoff + 40 * i
        nm = d[o:o + 8].rstrip(b"\x00").decode()
        vsz, vaddr, rsz, raddr = struct.unpack_from("<IIII", d, o + 8)
        out.append((nm, vaddr, vsz, raddr, rsz))
    return imagebase, out


for fn in glob.glob(DIR + r"\*.PE32"):
    d = open(fn, "rb").read()
    gi = d.find(APCB_G)
    if gi < 0:
        continue
    try:
        imagebase, secs = secs_of(d)
    except Exception:
        continue
    # GUID must be in a data section
    gi_rva = None
    for nm, vaddr, vsz, raddr, rsz in secs:
        if raddr <= gi < raddr + rsz:
            gi_rva = vaddr + (gi - raddr)
            break
    if gi_rva is None:
        continue
    # scan text for lea -> GUID RVA followed within a few insns by call [r+0x80] or [r+0x140]
    try:
        t = secs[0]
        code = d[t[3]:t[3] + t[4]]
        insns = list(md.disasm(code, imagebase + t[1]))
    except Exception:
        continue
    for idx, ins in enumerate(insns):
        if "rip" not in ins.op_str or ins.mnemonic not in ("lea", "mov"):
            continue
        mm = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", ins.op_str)
        if not mm:
            continue
        tgt = ins.address + ins.size + (int(mm.group(2), 16) if mm.group(1) == "+" else -int(mm.group(2), 16))
        if tgt != imagebase + gi_rva:
            continue
        # look ahead for gBS vtable call
        for j in range(idx + 1, min(idx + 8, len(insns))):
            n = insns[j]
            if n.mnemonic == "call" and n.op_str.startswith("qword ptr ["):
                offm = re.match(r"qword ptr \[\w+ \+ (0x[0-9a-f]+)\]", n.op_str)
                if offm and offm.group(1) in ("0x80", "0x140", "0x148"):
                    print("%-42s  lea@%#x -> call [%s] %s" % (fn.split("\\")[-1][:42], ins.address, offm.group(1), "(INSTALL-MULTI)" if offm.group(1) == "0x148" else ("(INSTALL)" if offm.group(1) == "0x80" else "(LOCATE)")))
                break
