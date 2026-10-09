# A2: t02 (PSP_FW_TRUSTED_OS) analysis from the hw dump.
#  1) locate $PS1 verifier (svc 0xF2 crypto service #6)
#  2) find its callers and error branches (fatal vs skip)
#  3) hunt loaders for dir entry types 0x24 (gasket) / 0x45 (TOS policy) and group types
#  4) hunt SMN bridge MMIO constants (0x0320xxxx/0x0322xxxx) = apply engine
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
ENV = ROM[0x8EAC00:0x8EAC00 + 0x14350]
assert ENV[0x10:0x14] == b"$PS1"
size = struct.unpack_from("<I", ENV, 0x14)[0]
ver = struct.unpack_from("<I", ENV, 0x60)[0]
TOS = ENV[0x100:0x100 + size]
print("t02: envelope size=%#x version=%#x body=%#x" % (size, ver, len(TOS)))
print("body head:", TOS[:16].hex())

r3 = open(r"C:\Users\OWNER\tmp_bc250\recon\robin3_psp_bodies\PSP_FW_TRUSTED_OS~0x2_0.1C.0.2.body", "rb").read()
print("robin3 t02 body: len=%#x equal-to-hw=%s" % (len(r3), r3 == TOS[:len(r3)] if len(r3) <= len(TOS) else (r3[:len(TOS)] == TOS)))


def disasm(data, base, mode_name):
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB if mode_name == "thumb" else capstone.CS_MODE_ARM)
    md.detail = False
    md.skipdata = True
    ins_list = []
    for ins in md.disasm(data, base):
        if ins.mnemonic == ".byte":
            continue
        ins_list.append(ins)
    return ins_list


# determine instruction mode windows: try ARM at 0 (vector table?) and scan both
ARM = disasm(TOS, 0, "arm")
THUMB = disasm(TOS, 0, "thumb")
print("decoded: ARM %d ins, Thumb %d ins (skipdata on)" % (len(ARM), len(THUMB)))

# 1) svc instructions (crypto service wrappers)
svc_hits = [(ins.address, ins.op_str) for ins in THUMB if ins.mnemonic == "svc"] + \
           [(ins.address, ins.op_str) for ins in ARM if ins.mnemonic == "svc"]
print("\n== svc instructions (Thumb list, then ARM) ==")
for a, o in svc_hits[:40]:
    print("  %#08x svc %s" % (a, o))

# 2) BL/B calls: build call map in Thumb (BL target calc) and ARM
def bl_targets(ins_list, thumb):
    out = []
    for i, ins in enumerate(ins_list):
        if ins.mnemonic == "bl":
            out.append((ins.address, ins.op_str))
    return out


TB = bl_targets(THUMB, True)
AB = bl_targets(ARM, False)
print("\n== BL counts: Thumb %d, ARM %d ==" % (len(TB), len(AB)))

# find function start containing svc 0xF2 usage: search around all svc sites for '0xf2'
f2_sites = []
for ins in THUMB:
    if ins.mnemonic == "svc" and ins.op_str.lower() in ("0xf2", "#0xf2", "242"):
        f2_sites.append(ins.address)
print("svc 0xF2 sites (thumb):", [hex(a) for a in f2_sites][:20])

# 3) literal-pool constants hunt: walk thumb ldr rX,[pc,#imm] and resolve
import re
def pools(ins_list, thumb):
    res = {}
    for ins in ins_list:
        m = re.match(r"^(\w+),\s*\[pc,\s*#(-?0x[0-9a-f]+|-?\d+)\]$", ins.op_str, re.I)
        if m:
            off = int(m.group(2), 0)
            pc = ins.address + (4 if thumb else 8)
            tgt = (pc + off) & ~1 if thumb else pc + off
            if 0 <= tgt <= len(TOS) - 4:
                val = struct.unpack_from("<I", TOS, tgt)[0] if tgt < len(TOS) - 3 else None
                if val is not None:
                    res.setdefault(val, []).append(ins.address)
    return res


TP = pools(THUMB, True)
AP = pools(ARM, False)
ALLP = {}
for d in (TP, AP):
    for k, v in d.items():
        ALLP.setdefault(k, []).extend(v)

WATCH = {0x45: "TOS_SECURITY_POLICY type", 0x24: "SEC_GASKET type", 0x210: "grp 0x210 (SEG bind)",
         0x201: "grp 0x201", 0x280: "grp 0x280", 0x281: "grp 0x281", 0x211: "grp 0x211",
         0x0900C234: "VCN bank commit", 0x0900CB80: "VCN bank lock", 0x03E810: "VCN_SEG reg",
         0x03A2011C: "DF aperture low", 0x31535024: "$PS1 magic", 0xAB1000: "APCB off",
         0x1C05: "APCB inst 5.00", 0x25DE: "APCB inst 4.00", 0x220E: "APCB inst 3.00"}
print("\n== watched constants in literal pools (code refs) ==")
for val, name in WATCH.items():
    if val is None:
        continue
    if val in ALLP:
        print("  %#010x %-28s <- referenced at %s" % (val, name, [hex(a) for a in ALLP[val][:8]]))
# SMN bridge range 0x0320xxxx/0x0322xxxx
print("\n== pool constants in 0x0320xxxx/0x0322xxxx (SMN bridge MMIO) ==")
for val in sorted(ALLP):
    if 0x03200000 <= val <= 0x0323FFFF:
        print("  %#010x <- at %s" % (val, [hex(a) for a in ALLP[val][:6]]))
print("\n== pool constants in 0x0900Cxxx (VCN bank) ==")
for val in sorted(ALLP):
    if 0x0900C000 <= val <= 0x0900CFFF:
        print("  %#010x <- at %s" % (val, [hex(a) for a in ALLP[val][:6]]))
