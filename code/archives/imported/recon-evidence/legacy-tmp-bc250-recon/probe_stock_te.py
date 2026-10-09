#!/usr/bin/env python3
"""Phase 17.0: probe stock ROMs for TE images and NBIO GFX module markers."""
import re

GUID = bytes.fromhex("F511C06191A64F54974FB9A42172CE53")
NAMES = [b"AmdNbioGfxARIPei", b"AmdNbioBaseARIPei", b"AmdNbioPcieARIPei",
         b"AmdFabricAriPei", b"GnbPei", b"NbPei", b"AmdCcxVhAriPei"]

for rom in [r"C:\Users\OWNER\tmp_bc250\recon\renoir_a3mstx_360\A3MSTX_3.60",
            r"C:\Users\OWNER\tmp_bc250\recon\cezanne_a3mstx_370e\A3MSTX_3.70E"]:
    data = open(rom, "rb").read()
    print(f"\n===== {rom} ({len(data)} bytes)")
    i = data.find(GUID)
    print("PEI-FV GUID at:", hex(i) if i >= 0 else "NOT FOUND")
    # second occurrence (FV header second GUID)
    j = data.find(GUID, i + 1)
    print("second GUID at:", hex(j) if j >= 0 else "none")
    # _FVH signature search
    fvh = [m.start() for m in re.finditer(b"_FVH", data)]
    print("_FVH signatures:", [hex(x) for x in fvh[:8]], f"({len(fvh)} total)")
    for n in NAMES:
        k = data.find(n)
        print(f"  UI name {n.decode():24s} at {hex(k) if k >= 0 else '-'}")
    # TE images: 'VZ' + x86 machine
    vz = [m.start() for m in re.finditer(b"VZ\x4c\x01", data)] + \
         [m.start() for m in re.finditer(b"VZ\x64\x86", data)]
    print("TE 'VZ' x86 images:", [hex(x) for x in vz[:40]], f"({len(vz)} total)")
