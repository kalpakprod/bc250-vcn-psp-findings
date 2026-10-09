# Scan all extracted DXE PE32 modules for:
#  - SMN gasket bank constants 0x0900C000..0x0900CFFF (VCN gasket per D2)
#  - DFG token ids 0x301..0x6FF (DFG token range from AmdApcbObrDxe dispatch)
#  - IOHC/MMIO-ish constants: 0x1C7xxxxx, 0x2C (gasket selector), perm masks 0x1F/0x3F/0x63/0x23
# Report per-module with offsets.
import os, struct, glob

DIR = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"

def u32s(d):
    for i in range(0, len(d) - 3):
        yield i, struct.unpack_from("<I", d, i)[0]

print("=== SMN 0x0900Cxxx (gasket VCN bank) ===")
for fn in glob.glob(DIR + r"\*.PE32"):
    d = open(fn, "rb").read()
    hits = [(i, v) for i, v in u32s(d) if 0x0900C000 <= v <= 0x0900CFFF]
    if hits:
        print(os.path.basename(fn)[-40:], ["%#x@+%#x" % (v, i) for i, v in hits[:8]])

print("\n=== 0x0900Bxxx / 0x0900Dxxx neighbors ===")
for fn in glob.glob(DIR + r"\*.PE32"):
    d = open(fn, "rb").read()
    hits = [(i, v) for i, v in u32s(d) if 0x09000000 <= v <= 0x0900FFFF and not (0x0900C000 <= v <= 0x0900CFFF)]
    if hits:
        print(os.path.basename(fn)[-40:], ["%#x@+%#x" % (v, i) for i, v in hits[:8]])

print("\n=== DFG token ids 0x301..0x6ff (u16 in code/data, count) ===")
for fn in glob.glob(DIR + r"\*.PE32"):
    d = open(fn, "rb").read()
    n = 0
    first = None
    for i in range(0, len(d) - 1):
        v = struct.unpack_from("<H", d, i)[0]
        if 0x301 <= v <= 0x6FF:
            n += 1
            if first is None:
                first = i
    if n:
        print("%-40s count=%d first@+%#x" % (os.path.basename(fn)[-40:], n, first))

print("\n=== explicit imms 0x305/0x306 (DFG types 5/6 as token ids) u32 ===")
for fn in glob.glob(DIR + r"\*.PE32"):
    d = open(fn, "rb").read()
    for gid in (0x305, 0x306, 0x301, 0x302, 0x303, 0x304):
        pat = struct.pack("<I", gid)
        i = d.find(pat)
        if i >= 0:
            print("%-40s 0x%x @+%#x ctx=%s" % (os.path.basename(fn)[-40:], gid, i, d[max(0, i - 4):i + 8].hex(" ")))

print("\n=== AmdFabric/ApcbObr/IOMMU/Agesa modules: 0x2C / 0x1C7 / 0x1f mask imms ===")
for fn in glob.glob(DIR + r"\*.PE32"):
    b = os.path.basename(fn)
    if not any(k in b for k in ("25075106", "a55a8", "83318", "73F53712", "C92C9385", "1DFB7BFA", "309214")):
        continue
    d = open(fn, "rb").read()
    for name, pat in (("0x2C imm8 3d/or", b"\x3d\x2c\x00\x00"), ("0x1C7xxxx", None), ("cmp 0x1f", b"\x3d\x1f\x00\x00")):
        pass
    # search u32 0x1C7xxxxx
    hits = [(i, v) for i, v in u32s(d) if 0x01C70000 <= v <= 0x01C7FFFF]
    print(b[-40:], "0x1C7xxxxx:", ["%#x@+%#x" % (v, i) for i, v in hits[:6]] or "-")
