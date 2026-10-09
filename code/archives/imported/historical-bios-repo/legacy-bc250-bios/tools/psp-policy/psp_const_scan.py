#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Constant scan in t01/t02/t28 PSP bodies (ARM code + literal pools)."""
import re, os

D = r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries\BC250_3.00_CHIPSETMENU.ROM" + "\\"
FILES = [
    ("00_t01_0x8E0400_A800.bin", "t01"),
    ("01_t02_0x8EAC00_14350.bin", "t02"),
    ("08_t28_0x984F00_1A770.bin", "t28"),
]
PATS = [
    ("$PS1-magic", b"$PS1"),
    ("APCB-ascii", b"APCB"),
    ("APCB-u32", bytes.fromhex("41435042")),
    ("hdr-00200020", bytes.fromhex("20002000")),
    ("DFG-1703-u32", bytes.fromhex("03170000")),
    ("DFG-1703+T5", bytes.fromhex("03170500")),
    ("PSPG-1701-u32", bytes.fromhex("01170000")),
    ("MEMG-1704-u32", bytes.fromhex("04170000")),
    ("SHA256-h0", bytes.fromhex("67452301")),
    ("SHA256-h1", bytes.fromhex("efcdab89")),
    ("SHA256-h2", bytes.fromhex("98badcfe")),
    ("AES-sbox", bytes.fromhex("637c777bf09f")),
    ("SHA1-K", bytes.fromhex("5a827999")),
    ("MD5-K", bytes.fromhex("d76aa478")),
    ("SMN-0900C234", bytes.fromhex("34c20009")),
    ("SMN-0900Cxxx-pat", bytes.fromhex("c20009")),
    ("0x1703-BE", bytes.fromhex("00001703")),
    ("grp-ver-0x0011", bytes.fromhex("1100")),
    ("0x0024-gasket", bytes.fromhex("24000000")),
]

for fn, nm in FILES:
    data = open(D + fn, "rb").read()
    print("=== %s (%d bytes) ===" % (nm, len(data)))
    for pn, b in PATS:
        hits = [m.start() for m in re.finditer(re.escape(b), data)]
        if hits:
            print("  %-18s hits=%d %s" % (pn, len(hits), [hex(h) for h in hits[:10]]))
    print()
